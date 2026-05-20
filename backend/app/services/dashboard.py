"""Dashboard service — summary, allocation, risk metrics, sector analysis."""

import math
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holding import Holding
from app.models.snapshot import Snapshot
from app.schemas.dashboard import (
    AllocationItem,
    DashboardSummary,
    RiskMetrics,
    SectorAllocation,
)


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


# ---------------------------------------------------------------------------
# Risk Metrics (#2)
# ---------------------------------------------------------------------------

RISK_FREE_RATE_ANNUAL = 0.015  # 1.5% — 一年期定存参考利率
TRADING_DAYS_PER_YEAR = 252


async def get_risk_metrics(db: AsyncSession) -> RiskMetrics | None:
    """Calculate portfolio risk metrics from snapshot daily returns.

    Returns None if insufficient data (< 5 trading days).
    """
    result = await db.execute(
        select(Snapshot)
        .order_by(Snapshot.date.desc())
        .limit(120)  # ~6 months of trading days
    )
    snapshots = list(reversed(result.scalars().all()))  # chronological

    # Filter snapshots with daily_return
    daily_returns = [s.daily_return for s in snapshots if s.daily_return is not None]

    if len(daily_returns) < 5:
        return None

    # --- Max Drawdown ---
    # Using total_market_value series for more accurate drawdown
    values = [float(s.total_market_value) for s in snapshots]
    peak = values[0]
    max_dd = 0.0
    for v in values:
        if v > peak:
            peak = v
        dd = (peak - v) / peak * 100 if peak > 0 else 0.0
        max_dd = max(max_dd, dd)

    # --- Annualized Volatility ---
    mean_ret = sum(daily_returns) / len(daily_returns)
    variance = sum((r - mean_ret) ** 2 for r in daily_returns) / len(daily_returns)
    daily_std = math.sqrt(variance)
    annual_vol = daily_std * math.sqrt(TRADING_DAYS_PER_YEAR)

    # --- Sharpe Ratio ---
    # annualized_return ≈ mean daily return × 252
    annual_return = mean_ret * TRADING_DAYS_PER_YEAR
    sharpe = (annual_return - RISK_FREE_RATE_ANNUAL * 100) / annual_vol if annual_vol > 0 else 0.0

    # --- VaR 95% (Historical) ---
    sorted_returns = sorted(daily_returns)
    idx_5pct = max(0, int(len(sorted_returns) * 0.05) - 1)
    var_95 = abs(sorted_returns[idx_5pct])  # positive number = potential loss %

    return RiskMetrics(
        max_drawdown=round(max_dd, 2),
        annualized_volatility=round(annual_vol, 2),
        sharpe_ratio=round(sharpe, 2),
        var_95=round(var_95, 2),
        period_days=len(daily_returns),
    )


# ---------------------------------------------------------------------------
# Sector Allocation (#4)
# ---------------------------------------------------------------------------

async def get_sector_allocation(db: AsyncSession) -> list[SectorAllocation]:
    """Calculate allocation by sector (申万一级行业)."""
    result = await db.execute(select(Holding))
    holdings = result.scalars().all()

    sector_values: dict[str, Decimal] = defaultdict(Decimal)
    sector_counts: dict[str, int] = defaultdict(int)
    total = Decimal("0")

    for h in holdings:
        if h.latest_price is not None:
            value = h.quantity * h.latest_price
        else:
            value = h.quantity * h.cost_price

        sector = h.sector or "未分类"
        sector_values[sector] += value
        sector_counts[sector] += 1
        total += value

    items = []
    for sector, market_value in sorted(
        sector_values.items(), key=lambda x: x[1], reverse=True
    ):
        pct = float(market_value / total * 100) if total > 0 else 0.0
        items.append(
            SectorAllocation(
                sector=sector,
                market_value=market_value,
                percentage=round(pct, 2),
                holdings_count=sector_counts[sector],
            )
        )

    return items
