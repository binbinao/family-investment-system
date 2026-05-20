"""Allocation target and deviation service."""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.allocation_target import AllocationTarget
from app.models.holding import Holding


async def get_targets(db: AsyncSession) -> list[AllocationTarget]:
    result = await db.execute(
        select(AllocationTarget).order_by(AllocationTarget.asset_type)
    )
    return list(result.scalars().all())


async def update_targets(
    db: AsyncSession, targets: list[dict]
) -> list[AllocationTarget]:
    """Update allocation targets. Expects list of {asset_type, target_ratio}."""
    for t in targets:
        result = await db.execute(
            select(AllocationTarget).where(
                AllocationTarget.asset_type == t["asset_type"]
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.target_ratio = Decimal(str(t["target_ratio"]))
            existing.updated_at = datetime.utcnow()
        else:
            db.add(
                AllocationTarget(
                    asset_type=t["asset_type"],
                    target_ratio=Decimal(str(t["target_ratio"])),
                )
            )

    await db.commit()
    return await get_targets(db)


async def get_deviation(db: AsyncSession) -> dict:
    """Calculate deviation between actual and target allocation."""
    targets = await get_targets(db)
    if not targets:
        return {"has_targets": False, "deviations": []}

    result = await db.execute(select(Holding))
    holdings = result.scalars().all()

    type_values: dict[str, Decimal] = defaultdict(Decimal)
    total = Decimal("0")

    for h in holdings:
        value = (
            h.quantity * h.latest_price
            if h.latest_price is not None
            else h.quantity * h.cost_price
        )
        type_values[h.asset_type] += value
        total += value

    deviations = []
    has_alert = False

    for t in targets:
        actual_value = type_values.get(t.asset_type, Decimal("0"))
        actual_pct = float(actual_value / total * 100) if total > 0 else 0.0
        target_pct = float(t.target_ratio)
        deviation = actual_pct - target_pct
        is_alert = abs(deviation) > 10

        if is_alert:
            has_alert = True

        adjust_amount = Decimal("0")
        adjust_direction = ""
        if total > 0 and abs(deviation) > 0.1:
            target_value = total * Decimal(str(target_pct)) / 100
            diff = target_value - actual_value
            if diff > 0:
                adjust_direction = "买入"
                adjust_amount = diff
            else:
                adjust_direction = "卖出"
                adjust_amount = abs(diff)

        deviations.append({
            "asset_type": t.asset_type,
            "target_pct": target_pct,
            "actual_pct": round(actual_pct, 2),
            "deviation": round(deviation, 2),
            "is_alert": is_alert,
            "adjust_direction": adjust_direction,
            "adjust_amount": adjust_amount,
        })

    return {
        "has_targets": True,
        "has_alert": has_alert,
        "deviations": deviations,
    }
