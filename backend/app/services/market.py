"""行情服务编排：缓存读写 + 多源抓取降级 + 持仓价格更新。

纯工具层已拆分到同目录子模块：
- ``market_symbols``：代码/市场解析
- ``market_parsers``：报文字段解析
- ``market_sources``：各数据源 HTTP 抓取
"""

import asyncio
import json
import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.core.time import utcnow
from app.models.holding import Holding
from app.models.price_cache import PriceCache
from app.services.market_sources import (
    _fetch_hk_quote_sina,
    _fetch_hk_quote_tencent,
    _fetch_stock_price_spot_fallback,
    _fetch_stock_quote_push2,
    _fetch_stock_quote_sina,
    _fetch_stock_quote_tencent,
    _fetch_us_quote_sina,
    _fetch_us_quote_tencent,
)
from app.services.market_symbols import (
    _equity_market,
    _hk_code_5,
    _normalize_stock_symbol,
    _us_ticker_pair,
)

logger = logging.getLogger(__name__)

STOCK_CACHE_TTL = 300  # 5 minutes
FUND_CACHE_TTL = 86400  # 24 hours
MAX_FAIL_COUNT = 3


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
        # 懒加载：akshare 会拉起 pandas 等重依赖，仅基金净值路径需要，避免拖慢应用启动
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
            data = json.loads(cached)
            holding.latest_price = Decimal(data["latest_price"])
            holding.latest_price_updated_at = datetime.fromisoformat(data["updated_at"])
            return True

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
        now = utcnow()
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
