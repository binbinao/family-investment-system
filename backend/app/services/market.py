"""AKShare market data service with Redis caching and degradation strategy."""

import logging
import math
import re
import time
from datetime import datetime
from decimal import Decimal

import requests

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.models.holding import Holding
from app.models.price_cache import PriceCache

logger = logging.getLogger(__name__)

STOCK_CACHE_TTL = 300  # 5 minutes
FUND_CACHE_TTL = 86400  # 24 hours
MAX_FAIL_COUNT = 3

_QUOTE_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def _equity_market(symbol: str) -> str:
    """标的所属市场：cn A 股、hk 港股、us 美股（用于选用行情接口）。"""
    raw = str(symbol).strip()
    u = raw.upper()
    if u.endswith(".HK"):
        return "hk"
    for suf in (".US", ".NYSE", ".NASDAQ", ".OQ"):
        if u.endswith(suf):
            return "us"
    if u.endswith(".N") and len(u) > 4:
        return "us"
    for suf in (".SH", ".SZ", ".BJ", ".SS"):
        if u.endswith(suf):
            return "cn"
    letters = re.sub(r"[^A-Za-z]", "", raw)
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits and not letters:
        if len(digits) == 6:
            return "cn"
        if len(digits) == 5:
            return "hk"
    if letters:
        return "us"
    return "cn"


def _hk_code_5(symbol: str) -> str:
    """港股 5 位代码，如 00700、00001。"""
    raw = str(symbol).strip().upper()
    base = raw[: -3] if raw.endswith(".HK") else raw
    d = "".join(ch for ch in base if ch.isdigit())
    if not d:
        return ""
    if len(d) > 5:
        d = d[-5:]
    return d.zfill(5)


def _us_ticker_pair(symbol: str) -> tuple[str, str]:
    """(腾讯 q 参数前缀+代码, 新浪 gb_ 后缀)。腾讯示例 usAAPL、usBRK.B；新浪 gb_aapl、gb_brkb。"""
    raw = str(symbol).strip().upper()
    for suf in (".US", ".NYSE", ".NASDAQ", ".OQ"):
        if raw.endswith(suf):
            raw = raw[: -len(suf)]
            break
    if raw.endswith(".N") and len(raw) > 4:
        raw = raw[:-2]
    tick = raw.replace("-", ".")
    if not tick or not re.search(r"[A-Z]", tick):
        return "", ""
    tencent = "us" + tick
    sina_suffix = tick.lower().replace(".", "")
    return tencent, sina_suffix


def _normalize_stock_symbol(symbol: str) -> str:
    """将用户输入规范为 A 股 6 位代码，便于与东财 spot 表「代码」列匹配。"""
    if _equity_market(symbol) != "cn":
        return str(symbol).strip()
    raw = str(symbol).strip().upper()
    for suf in (".SH", ".SZ", ".BJ", ".SS"):
        if raw.endswith(suf):
            raw = raw[: -len(suf)]
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return str(symbol).strip()
    if len(digits) <= 6:
        return digits.zfill(6)
    return digits[-6:]


def _spot_em_code_key(col):
    """统一行情表代码列为 6 位字符串（兼容 int/float/str）。"""
    s = col.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()

    def to_key(x: str) -> str:
        x = str(x).strip()
        if x.isdigit():
            return x.zfill(6)
        return x

    return s.map(to_key)


def _vendor_list_code(norm: str) -> str:
    """新浪/腾讯 list 参数：沪 sh、深 sz、北交所 920 段为 bj。"""
    if norm.startswith("920"):
        return f"bj{norm}"
    if norm.startswith("6"):
        return f"sh{norm}"
    return f"sz{norm}"


def _decimal_from_str(s: str | None) -> Decimal | None:
    if s is None:
        return None
    t = str(s).strip()
    if not t or t in ("-", "--"):
        return None
    try:
        return Decimal(t)
    except Exception:
        return None


def _parse_tencent_hk_us_line(inner: str) -> dict | None:
    """腾讯 r_hk / us 行情：~ 分隔，日期时间后接涨跌额、涨跌幅（与 A 股下标不同）。"""
    parts = inner.split("~")
    if len(parts) < 10:
        return None
    latest = _decimal_from_str(parts[3])
    if latest is None:
        return None
    prev = _decimal_from_str(parts[4])
    change: Decimal | None = None
    pct: Decimal | None = None
    for i, p in enumerate(parts):
        if p and re.search(r"\d{4}[-/]\d{2}[-/]\d{2}", p):
            if i + 2 < len(parts):
                change = _decimal_from_str(parts[i + 1])
                pct = _decimal_from_str(parts[i + 2])
            break
    if change is None and prev is not None:
        change = latest - prev
    if pct is None and prev is not None and prev > 0 and change is not None:
        pct = (change / prev) * Decimal(100)
    name = parts[1].strip() if len(parts) > 1 and parts[1] else None
    return {
        "latest_price": latest,
        "price_change": change if change is not None else Decimal("0"),
        "price_change_pct": pct if pct is not None else Decimal("0"),
        "name": name,
    }


def _fetch_hk_quote_sina(symbol: str, hk5: str) -> dict | None:
    """新浪港股 hq.sinajs.cn/list=hk00700。"""
    if not hk5:
        return None
    url = f"https://hq.sinajs.cn/list=hk{hk5}"
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            r = requests.get(
                url,
                headers=SINA_QUOTE_HEADERS,
                timeout=(8, 20),
            )
            r.raise_for_status()
            text = r.content.decode("gb18030", errors="replace")
            m = re.search(r'="([^"]*)"', text)
            if not m:
                return None
            body = m.group(1).strip()
            if not body:
                return None
            parts = body.split(",")
            if len(parts) < 9:
                return None
            name_cn = parts[1].strip() if parts[1] else parts[0].strip()
            latest = _decimal_from_str(parts[6])
            if latest is None:
                return None
            change = _decimal_from_str(parts[7])
            pct = _decimal_from_str(parts[8])
            if change is None:
                prev = _decimal_from_str(parts[3])
                if prev is not None:
                    change = latest - prev
            if pct is None and change is not None:
                prev = _decimal_from_str(parts[3])
                if prev is not None and prev > 0:
                    pct = (change / prev) * Decimal(100)
            out: dict = {
                "latest_price": latest,
                "price_change": change if change is not None else Decimal("0"),
                "price_change_pct": pct if pct is not None else Decimal("0"),
            }
            if name_cn:
                out["name"] = name_cn
            return out
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(0.3 * (attempt + 1))
    logger.warning(
        "Sina HK quote failed raw=%r hk=%r: %s",
        symbol,
        hk5,
        last_err,
    )
    return None


def _fetch_hk_quote_tencent(symbol: str, hk5: str) -> dict | None:
    if not hk5:
        return None
    code = f"r_hk{hk5}"
    bases = ("https://sqt.gtimg.cn/q=", "https://qt.gtimg.cn/q=")
    last_err: Exception | None = None
    for base in bases:
        url = f"{base}{code}"
        for attempt in range(3):
            try:
                r = requests.get(
                    url,
                    headers=TENCENT_QUOTE_HEADERS,
                    timeout=(8, 20),
                )
                r.raise_for_status()
                text = r.content.decode("gb18030", errors="replace")
                m = re.search(r'="([^"]*)"', text)
                if not m:
                    return None
                inner = m.group(1).strip()
                if not inner:
                    return None
                parsed = _parse_tencent_hk_us_line(inner)
                if not parsed:
                    return None
                out = {k: v for k, v in parsed.items() if v is not None}
                if "name" not in out and parsed.get("name"):
                    out["name"] = parsed["name"]
                return out
            except Exception as e:
                last_err = e
                if attempt < 2:
                    time.sleep(0.3 * (attempt + 1))
    logger.warning(
        "Tencent HK quote failed raw=%r hk=%r: %s",
        symbol,
        hk5,
        last_err,
    )
    return None


def _fetch_us_quote_tencent(symbol: str, tencent_code: str) -> dict | None:
    """腾讯美股 q=usAAPL（含点号 ticker）。"""
    if not tencent_code or not tencent_code.startswith("us"):
        return None
    bases = ("https://sqt.gtimg.cn/q=", "https://qt.gtimg.cn/q=")
    last_err: Exception | None = None
    for base in bases:
        url = f"{base}{tencent_code}"
        for attempt in range(3):
            try:
                r = requests.get(
                    url,
                    headers=TENCENT_QUOTE_HEADERS,
                    timeout=(8, 20),
                )
                r.raise_for_status()
                text = r.content.decode("gb18030", errors="replace")
                m = re.search(r'="([^"]*)"', text)
                if not m:
                    return None
                inner = m.group(1).strip()
                if not inner:
                    return None
                parsed = _parse_tencent_hk_us_line(inner)
                if not parsed:
                    return None
                out = {k: v for k, v in parsed.items() if k != "name" or v}
                if parsed.get("name"):
                    out["name"] = parsed["name"]
                return out
            except Exception as e:
                last_err = e
                if attempt < 2:
                    time.sleep(0.3 * (attempt + 1))
    logger.warning(
        "Tencent US quote failed raw=%r code=%r: %s",
        symbol,
        tencent_code,
        last_err,
    )
    return None


def _fetch_us_quote_sina(symbol: str, sina_suffix: str) -> dict | None:
    """新浪美股 gb_aapl（后缀为小写、去点）。"""
    if not sina_suffix:
        return None
    url = f"https://hq.sinajs.cn/list=gb_{sina_suffix}"
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            r = requests.get(
                url,
                headers=SINA_QUOTE_HEADERS,
                timeout=(8, 20),
            )
            r.raise_for_status()
            text = r.content.decode("gb18030", errors="replace")
            m = re.search(r'="([^"]*)"', text)
            if not m:
                return None
            body = m.group(1).strip()
            if not body:
                return None
            parts = body.split(",")
            if len(parts) < 5:
                return None
            name = parts[0].strip() or None
            latest = _decimal_from_str(parts[1])
            if latest is None or latest <= 0:
                return None
            pct = _decimal_from_str(parts[2])
            change = _decimal_from_str(parts[4])
            if change is None:
                change = Decimal("0")
            if pct is None:
                pct = Decimal("0")
            out: dict = {
                "latest_price": latest,
                "price_change": change,
                "price_change_pct": pct,
            }
            if name:
                out["name"] = name
            return out
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(0.3 * (attempt + 1))
    logger.warning(
        "Sina US quote failed raw=%r gb=%r: %s",
        symbol,
        sina_suffix,
        last_err,
    )
    return None


TENCENT_QUOTE_HEADERS = {
    "User-Agent": _QUOTE_BROWSER_UA,
    "Referer": "https://stockapp.finance.qq.com/",
    "Accept": "*/*",
}

SINA_QUOTE_HEADERS = {
    "User-Agent": _QUOTE_BROWSER_UA,
    "Referer": "https://finance.sina.com.cn/",
    "Accept": "*/*",
}


def _fetch_stock_quote_tencent(symbol: str, norm: str) -> dict | None:
    """腾讯财经单票接口（gb18030），字段说明见公开文档。"""
    code = _vendor_list_code(norm)
    bases = (
        "https://sqt.gtimg.cn/q=",
        "https://qt.gtimg.cn/q=",
    )
    last_err: Exception | None = None
    for base in bases:
        url = f"{base}{code}"
        for attempt in range(3):
            try:
                r = requests.get(
                    url,
                    headers=TENCENT_QUOTE_HEADERS,
                    timeout=(8, 20),
                )
                r.raise_for_status()
                text = r.content.decode("gb18030", errors="replace")
                m = re.search(r'="([^"]*)"', text)
                if not m:
                    return None
                inner = m.group(1).strip()
                if not inner:
                    return None
                parts = inner.split("~")
                if len(parts) < 33:
                    return None
                latest = _decimal_from_str(parts[3])
                if latest is None:
                    return None
                prev = _decimal_from_str(parts[4])
                change = _decimal_from_str(parts[31])
                pct = _decimal_from_str(parts[32])
                if change is None and prev is not None:
                    change = latest - prev
                if pct is None and prev is not None and prev > 0 and change is not None:
                    pct = (change / prev) * Decimal(100)
                name = parts[1].strip() if len(parts) > 1 and parts[1] else None
                out: dict = {
                    "latest_price": latest,
                    "price_change": change if change is not None else Decimal("0"),
                    "price_change_pct": pct if pct is not None else Decimal("0"),
                }
                if name:
                    out["name"] = name
                return out
            except Exception as e:
                last_err = e
                if attempt < 2:
                    time.sleep(0.3 * (attempt + 1))
    logger.warning(
        "Tencent quote failed after retries raw=%r norm=%r: %s",
        symbol,
        norm,
        last_err,
    )
    return None


def _fetch_stock_quote_sina(symbol: str, norm: str) -> dict | None:
    """新浪财经 hq.sinajs.cn 单票接口（gb18030）。"""
    code = _vendor_list_code(norm)
    url = f"https://hq.sinajs.cn/list={code}"
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            r = requests.get(
                url,
                headers=SINA_QUOTE_HEADERS,
                timeout=(8, 20),
            )
            r.raise_for_status()
            text = r.content.decode("gb18030", errors="replace")
            m = re.search(r'="([^"]*)"', text)
            if not m:
                return None
            body = m.group(1).strip()
            if not body:
                return None
            parts = body.split(",")
            if len(parts) < 4:
                return None
            name = parts[0].strip() or None
            prev = _decimal_from_str(parts[2])
            latest = _decimal_from_str(parts[3])
            if latest is None:
                return None
            change = (
                (latest - prev) if prev is not None else Decimal("0")
            )
            pct = (
                (change / prev * Decimal(100))
                if prev is not None and prev > 0
                else Decimal("0")
            )
            out: dict = {
                "latest_price": latest,
                "price_change": change,
                "price_change_pct": pct,
            }
            if name:
                out["name"] = name
            return out
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(0.3 * (attempt + 1))
    logger.warning(
        "Sina quote failed after retries raw=%r norm=%r: %s",
        symbol,
        norm,
        last_err,
    )
    return None


def _eastmoney_market_prefix(norm: str) -> int:
    """东财 secid 市场前缀：沪市 1，其余（深/北交所 920 等）0。与 AKShare 单票接口一致。"""
    return 1 if norm.startswith("6") else 0


EASTMONEY_QUOTE_HEADERS = {
    "User-Agent": _QUOTE_BROWSER_UA,
    "Referer": "https://quote.eastmoney.com/",
    "Accept": "*/*",
}


def _parse_em_scaled_price(raw) -> Decimal | None:
    """东财 qt/stock/get 在 fltt=2 下，金额类字段多为实际值 ×100。"""
    if raw is None:
        return None
    if isinstance(raw, float) and math.isnan(raw):
        return None
    try:
        return Decimal(str(raw)) / Decimal(100)
    except Exception:
        return None


def _fetch_stock_quote_push2(symbol: str, norm: str) -> dict | None:
    """单票 push2 接口，避免全市场 clist 大响应易被限流/断连。"""
    market = _eastmoney_market_prefix(norm)
    params = {
        "fltt": "2",
        "invt": "2",
        "fields": "f43,f169,f170,f57,f58,f60",
        "secid": f"{market}.{norm}",
    }
    # 与 AKShare 全量行情同域的 82.push2 在部分网络下比 push2 更稳定
    base_urls = (
        "https://push2.eastmoney.com/api/qt/stock/get",
        "https://82.push2.eastmoney.com/api/qt/stock/get",
    )
    last_err: Exception | None = None
    for base in base_urls:
        for attempt in range(3):
            try:
                r = requests.get(
                    base,
                    params=params,
                    headers=EASTMONEY_QUOTE_HEADERS,
                    timeout=(8, 20),
                )
                r.raise_for_status()
                payload = r.json()
                data = payload.get("data")
                if not isinstance(data, dict) or data.get("f43") is None:
                    logger.warning(
                        "Eastmoney quote empty rc=%s host=%s raw=%r norm=%r",
                        payload.get("rc"),
                        base.split("/")[2],
                        symbol,
                        norm,
                    )
                    return None
                latest = _parse_em_scaled_price(data.get("f43"))
                if latest is None:
                    return None
                prev_close = _parse_em_scaled_price(data.get("f60"))
                change = _parse_em_scaled_price(data.get("f169"))
                if change is None and prev_close is not None:
                    change = latest - prev_close
                pct = _parse_em_scaled_price(data.get("f170"))
                if (
                    pct is None
                    and prev_close is not None
                    and prev_close > 0
                    and change is not None
                ):
                    pct = (change / prev_close) * Decimal(100)
                name_raw = data.get("f58")
                name = str(name_raw).strip() if name_raw else None
                out: dict = {
                    "latest_price": latest,
                    "price_change": change if change is not None else Decimal("0"),
                    "price_change_pct": pct if pct is not None else Decimal("0"),
                }
                if name:
                    out["name"] = name
                return out
            except Exception as e:
                last_err = e
                if attempt < 2:
                    time.sleep(0.35 * (attempt + 1))
    logger.warning(
        "Eastmoney push2 quote failed after retries raw=%r norm=%r: %s",
        symbol,
        norm,
        last_err,
    )
    return None


def _fetch_stock_price_spot_fallback(symbol: str, norm: str) -> dict | None:
    """全市场 A 股列表兜底（网络差时易失败，仅作后备）。"""
    try:
        import akshare as ak

        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty or "代码" not in df.columns:
            logger.warning("stock_zh_a_spot_em returned empty or missing 代码 column")
            return None
        codes = _spot_em_code_key(df["代码"])
        row = df[codes == norm]
        if row.empty:
            logger.warning(
                "No spot row for symbol raw=%r normalized=%r (sample codes: %s)",
                symbol,
                norm,
                codes.head(3).tolist(),
            )
            return None
        r = row.iloc[0]
        return {
            "latest_price": Decimal(str(r["最新价"])),
            "price_change": Decimal(str(r["涨跌额"])),
            "price_change_pct": Decimal(str(r["涨跌幅"])),
            "name": str(r["名称"]),
            "source": "eastmoney_spot",
        }
    except Exception as e:
        logger.warning(f"AKShare spot fallback failed for {symbol}: {e}")
        return None


def _fetch_stock_price_sync(symbol: str) -> dict | None:
    """A 股：腾讯 → 新浪 → 东财；港股/美股：新浪 → 腾讯（独立接口）。"""
    m = _equity_market(symbol)
    if m == "hk":
        hk5 = _hk_code_5(symbol)
        if not hk5:
            logger.warning("港股代码无法解析 raw=%r", symbol)
            return None
        for fetcher, src in (
            (_fetch_hk_quote_sina, "sina_hk"),
            (_fetch_hk_quote_tencent, "tencent_hk"),
        ):
            q = fetcher(symbol, hk5)
            if q:
                q["source"] = src
                return q
        return None
    if m == "us":
        tenc, sina_suf = _us_ticker_pair(symbol)
        if not tenc:
            logger.warning("美股代码无法解析 raw=%r", symbol)
            return None
        q = _fetch_us_quote_tencent(symbol, tenc)
        if q:
            q["source"] = "tencent_us"
            return q
        if sina_suf:
            q = _fetch_us_quote_sina(symbol, sina_suf)
            if q:
                q["source"] = "sina_us"
                return q
        return None

    norm = _normalize_stock_symbol(symbol)
    chain = (
        (_fetch_stock_quote_tencent, "tencent"),
        (_fetch_stock_quote_sina, "sina"),
        (_fetch_stock_quote_push2, "eastmoney"),
    )
    for fetcher, src in chain:
        q = fetcher(symbol, norm)
        if q:
            q["source"] = src
            return q
    return _fetch_stock_price_spot_fallback(symbol, norm)


def _fetch_fund_nav_sync(symbol: str) -> dict | None:
    """Fetch fund NAV from AKShare (synchronous, runs in thread)."""
    try:
        import akshare as ak

        df = ak.fund_open_fund_info_em(symbol=symbol, indicator="单位净值走势")
        if df.empty:
            return None
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        nav = Decimal(str(latest["单位净值"]))
        prev_nav = Decimal(str(prev["单位净值"]))
        change = nav - prev_nav
        change_pct = (change / prev_nav * 100) if prev_nav > 0 else Decimal("0")
        return {
            "latest_price": nav,
            "price_change": change,
            "price_change_pct": change_pct,
        }
    except Exception as e:
        logger.warning(f"AKShare fund fetch failed for {symbol}: {e}")
        return None


async def update_holding_price(
    db: AsyncSession,
    holding: Holding,
    *,
    force: bool = False,
) -> bool:
    """Update a single holding's price from AKShare with Redis cache.

    force=True：跳过/清除 Redis，用于用户手动「刷新行情」，避免界面仍显示缓存旧价。
    """
    redis_client = get_redis()
    cache_key = f"price:{holding.symbol}"

    if force:
        await redis_client.delete(cache_key)

    if not force:
        cached = await redis_client.get(cache_key)
        if cached:
            import json

            data = json.loads(cached)
            holding.latest_price = Decimal(data["latest_price"])
            holding.latest_price_updated_at = datetime.fromisoformat(data["updated_at"])
            return True

    import asyncio

    if holding.asset_type == "股票":
        result = await asyncio.to_thread(_fetch_stock_price_sync, holding.symbol)
        ttl = STOCK_CACHE_TTL
    elif holding.asset_type == "基金":
        result = await asyncio.to_thread(_fetch_fund_nav_sync, holding.symbol)
        ttl = FUND_CACHE_TTL
    else:
        return False

    cache_result = await db.execute(
        select(PriceCache).where(PriceCache.symbol == holding.symbol)
    )
    price_cache = cache_result.scalar_one_or_none()

    if result:
        now = datetime.utcnow()
        holding.latest_price = result["latest_price"]
        holding.latest_price_updated_at = now

        if price_cache:
            price_cache.latest_price = result["latest_price"]
            price_cache.price_change = result.get("price_change")
            price_cache.price_change_pct = result.get("price_change_pct")
            price_cache.updated_at = now
            price_cache.source = result.get("source", "akshare")
            price_cache.fail_count = 0
            if result.get("name"):
                price_cache.name = result["name"]
        else:
            price_cache = PriceCache(
                symbol=holding.symbol,
                name=result.get("name", holding.name),
                latest_price=result["latest_price"],
                price_change=result.get("price_change"),
                price_change_pct=result.get("price_change_pct"),
                updated_at=now,
                source=result.get("source", "akshare"),
                fail_count=0,
            )
            db.add(price_cache)

        import json

        await redis_client.setex(
            cache_key,
            ttl,
            json.dumps(
                {
                    "latest_price": str(result["latest_price"]),
                    "updated_at": now.isoformat(),
                }
            ),
        )
        return True
    else:
        if price_cache:
            price_cache.fail_count += 1
        logger.warning(
            f"Price fetch failed for {holding.symbol}, "
            f"fail_count={price_cache.fail_count if price_cache else 'N/A'}"
        )
        return False


async def refresh_all_prices(db: AsyncSession, *, force: bool = False) -> dict:
    """Refresh prices for all holdings. Returns summary.

    force=True：跳过 Redis 缓存，拉取最新行情（用于接口手动刷新）。
    """
    result = await db.execute(select(Holding))
    holdings = result.scalars().all()

    success_count = 0
    fail_count = 0
    skipped_count = 0

    for h in holdings:
        if h.asset_type not in ("股票", "基金"):
            skipped_count += 1
            continue
        ok = await update_holding_price(db, h, force=force)
        if ok:
            success_count += 1
        else:
            fail_count += 1

    await db.commit()

    return {
        "total": len(holdings),
        "success": success_count,
        "failed": fail_count,
        "skipped": skipped_count,
    }


async def get_market_status(db: AsyncSession) -> list[dict]:
    """Get market update status for all cached symbols."""
    result = await db.execute(select(PriceCache).order_by(PriceCache.updated_at.desc()))
    caches = result.scalars().all()
    return [
        {
            "symbol": c.symbol,
            "name": c.name,
            "latest_price": c.latest_price,
            "price_change": c.price_change,
            "price_change_pct": c.price_change_pct,
            "updated_at": c.updated_at,
            "source": c.source,
            "fail_count": c.fail_count,
            "is_stale": c.fail_count >= MAX_FAIL_COUNT,
        }
        for c in caches
    ]
