"""AKShare market data service with Redis caching and degradation strategy."""

import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.models.holding import Holding
from app.models.price_cache import PriceCache

logger = logging.getLogger(__name__)

STOCK_CACHE_TTL = 300  # 5 minutes
FUND_CACHE_TTL = 86400  # 24 hours
MAX_FAIL_COUNT = 3


def _fetch_stock_price_sync(symbol: str) -> dict | None:
    """Fetch stock price from AKShare (synchronous, runs in thread)."""
    try:
        import akshare as ak

        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == symbol]
        if row.empty:
            return None
        r = row.iloc[0]
        return {
            "latest_price": Decimal(str(r["最新价"])),
            "price_change": Decimal(str(r["涨跌额"])),
            "price_change_pct": Decimal(str(r["涨跌幅"])),
            "name": str(r["名称"]),
        }
    except Exception as e:
        logger.warning(f"AKShare stock fetch failed for {symbol}: {e}")
        return None


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
) -> bool:
    """Update a single holding's price from AKShare with Redis cache."""
    redis_client = get_redis()
    cache_key = f"price:{holding.symbol}"

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
            price_cache.source = "akshare"
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
                source="akshare",
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


async def refresh_all_prices(db: AsyncSession) -> dict:
    """Refresh prices for all holdings. Returns summary."""
    result = await db.execute(select(Holding))
    holdings = result.scalars().all()

    success_count = 0
    fail_count = 0
    skipped_count = 0

    for h in holdings:
        if h.asset_type not in ("股票", "基金"):
            skipped_count += 1
            continue
        ok = await update_holding_price(db, h)
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
