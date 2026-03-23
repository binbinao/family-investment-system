from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holding import Holding
from app.schemas.dashboard import AllocationItem, DashboardSummary


async def get_summary(db: AsyncSession) -> DashboardSummary:
    result = await db.execute(select(Holding))
    holdings = result.scalars().all()

    total_market_value = Decimal("0")
    total_cost = Decimal("0")
    has_price_data = False

    for h in holdings:
        cost = h.quantity * h.cost_price
        total_cost += cost

        if h.latest_price is not None:
            total_market_value += h.quantity * h.latest_price
            has_price_data = True
        else:
            total_market_value += cost

    total_profit_loss = total_market_value - total_cost
    total_profit_loss_pct = (
        float(total_profit_loss / total_cost) if total_cost > 0 else 0.0
    )

    return DashboardSummary(
        total_market_value=total_market_value,
        total_cost=total_cost,
        total_profit_loss=total_profit_loss,
        total_profit_loss_pct=total_profit_loss_pct,
        holdings_count=len(holdings),
    )


async def get_allocation(db: AsyncSession) -> list[AllocationItem]:
    result = await db.execute(select(Holding))
    holdings = result.scalars().all()

    type_values: dict[str, Decimal] = defaultdict(Decimal)
    total = Decimal("0")

    for h in holdings:
        if h.latest_price is not None:
            value = h.quantity * h.latest_price
        else:
            value = h.quantity * h.cost_price
        type_values[h.asset_type] += value
        total += value

    items = []
    for asset_type, market_value in sorted(
        type_values.items(), key=lambda x: x[1], reverse=True
    ):
        pct = float(market_value / total * 100) if total > 0 else 0.0
        items.append(
            AllocationItem(
                asset_type=asset_type,
                market_value=market_value,
                percentage=round(pct, 2),
            )
        )

    return items
