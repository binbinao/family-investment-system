"""各行情数据源抓取：腾讯 / 新浪 / 东财 push2 / AKShare 兜底。含重试与超时。"""

import logging
import re
import time
from decimal import Decimal

import requests

from app.services.market_parsers import (
    _decimal_from_str,
    _parse_em_scaled_price,
    _parse_tencent_hk_us_line,
)
from app.services.market_symbols import (
    _eastmoney_market_prefix,
    _spot_em_code_key,
    _vendor_list_code,
)

logger = logging.getLogger(__name__)

_QUOTE_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

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

EASTMONEY_QUOTE_HEADERS = {
    "User-Agent": _QUOTE_BROWSER_UA,
    "Referer": "https://quote.eastmoney.com/",
    "Accept": "*/*",
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
        # 懒加载：akshare 会拉起 pandas 等重依赖，仅兜底路径需要，避免拖慢应用启动
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
