"""Daily portfolio snapshot service."""

import json
import logging
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holding import Holding
from app.models.snapshot import Snapshot

logger = logging.getLogger(__name__)


async def create_daily_snapshot(db: AsyncSession) -> Snapshot | None:
    """Create a snapshot of current portfolio. Skips if today's snapshot exists."""
    today = date.today()

    existing = await db.execute(
        select(Snapshot).where(Snapshot.date == today)
    )
    if existing.scalar_one_or_none():
        logger.info(f"Snapshot for {today} already exists, skipping")
        return None

    result = await db.execute(select(Holding))
    holdings = result.scalars().all()

    if not holdings:
        logger.info("No holdings, skipping snapshot")
        return None

    total_market_value = Decimal("0")
    total_cost = Decimal("0")
    holdings_data = []

    for h in holdings:
        cost = h.quantity * h.cost_price
        total_cost += cost

        if h.latest_price is not None:
            mv = h.quantity * h.latest_price
        else:
            mv = cost
        total_market_value += mv

        holdings_data.append({
            "symbol": h.symbol,
            "name": h.name,
            "asset_type": h.asset_type,
            "quantity": str(h.quantity),
            "cost_price": str(h.cost_price),
            "latest_price": str(h.latest_price) if h.latest_price else None,
            "market_value": str(mv),
        })

    snapshot = Snapshot(
        date=today,
        total_market_value=total_market_value,
        total_cost=total_cost,
        total_profit_loss=total_market_value - total_cost,
        holdings_json=json.dumps(holdings_data, ensure_ascii=False),
    )
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)

    logger.info(f"Created snapshot for {today}: market_value={total_market_value}")
    return snapshot


async def list_snapshots(
    db: AsyncSession,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[Snapshot]:
    """List snapshots, optionally filtered by date range."""
    query = select(Snapshot).order_by(Snapshot.date.asc())
    if start_date:
        query = query.where(Snapshot.date >= start_date)
    if end_date:
        query = query.where(Snapshot.date <= end_date)

    result = await db.execute(query)
    return list(result.scalars().all())
