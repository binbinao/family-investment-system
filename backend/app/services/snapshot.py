"""Daily portfolio snapshot service."""

import json
import logging
import math
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holding import Holding
from app.models.snapshot import Snapshot

logger = logging.getLogger(__name__)

CHART_LOOKBACK_DAYS = 30


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


async def portfolio_totals_from_holdings(
    db: AsyncSession,
) -> tuple[Decimal, Decimal] | None:
    """(total_cost, total_market_value) from current holdings; None if no holdings."""
    result = await db.execute(select(Holding))
    holdings = result.scalars().all()
    if not holdings:
        return None

    total_market_value = Decimal("0")
    total_cost = Decimal("0")
    for h in holdings:
        cost = h.quantity * h.cost_price
        total_cost += cost
        if h.latest_price is not None:
            total_market_value += h.quantity * h.latest_price
        else:
            total_market_value += cost
    return total_cost, total_market_value


def _chart_row(
    d: date,
    mv: Decimal,
    cost: Decimal,
    *,
    estimated: bool,
) -> dict:
    pl = mv - cost
    return {
        "date": d.isoformat(),
        "total_market_value": float(mv),
        "total_cost": float(cost),
        "total_profit_loss": float(pl),
        "estimated": estimated,
    }


async def build_last_30_days_chart(db: AsyncSession) -> list[dict]:
    """
    近 30 个自然日（含今天）资产走势：有快照的日用库内数据，其余按当前持仓的总成本→总市值
    做平滑过渡并加轻微确定性波动模拟；今天始终用实时持仓，与总览卡片一致。
    """
    totals = await portfolio_totals_from_holdings(db)
    if totals is None:
        return []

    cost_now, mv_now = totals
    end = date.today()
    start = end - timedelta(days=CHART_LOOKBACK_DAYS - 1)
    day_list = [start + timedelta(days=i) for i in range(CHART_LOOKBACK_DAYS)]
    n = len(day_list)

    result = await db.execute(
        select(Snapshot).where(Snapshot.date >= start, Snapshot.date <= end)
    )
    by_date: dict[date, Snapshot] = {s.date: s for s in result.scalars().all()}

    out: list[dict] = []
    last_idx = n - 1

    for i, d in enumerate(day_list):
        if d == end:
            snap = by_date.get(d)
            out.append(
                _chart_row(
                    end,
                    mv_now,
                    cost_now,
                    estimated=snap is None,
                )
            )
            continue

        snap = by_date.get(d)
        if snap is not None:
            out.append(
                _chart_row(
                    d,
                    snap.total_market_value,
                    snap.total_cost,
                    estimated=False,
                )
            )
            continue

        # 无快照的历史日：从「30 日前≈总成本」到「昨日前贴近当前市值」的插值 + 微波动
        denom = last_idx if last_idx > 0 else 1
        t = Decimal(str(i / denom))
        mv_linear = cost_now + (mv_now - cost_now) * t
        wobble = Decimal(str(math.sin(i * 0.63 + 1.2) * 0.008))
        mv_est = mv_linear * (Decimal("1") + wobble)
        out.append(_chart_row(d, mv_est, cost_now, estimated=True))

    return out
