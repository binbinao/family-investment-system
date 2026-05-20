"""Tax-aware rebalance service — considers trading costs & tax implications."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.allocation_target import AllocationTarget
from app.models.holding import Holding
from app.schemas.dashboard import (
    RebalanceResult,
    RebalanceSuggestion,
    TradeCostDetail,
)

# ---------------------------------------------------------------------------
# A股/基金交易成本常量
# ---------------------------------------------------------------------------

# 印花税：卖出时单边征收 0.05% (2023年8月28日起减半)
STAMP_TAX_RATE = Decimal("0.0005")

# 佣金：买卖双向，一般0.025% (万2.5)，最低5元
COMMISSION_RATE = Decimal("0.00025")
COMMISSION_MIN = Decimal("5")

# 基金赎回费率（按持有期递减）
# 持有<7天: 1.5%, 7-30天: 0.75%, 30-365天: 0.5%, 1-2年: 0.25%, >2年: 0%
REDEMPTION_FEE_SCHEDULE = [
    (7, Decimal("0.015")),     # < 7天
    (30, Decimal("0.0075")),   # 7-30天
    (365, Decimal("0.005")),   # 30天-1年
    (730, Decimal("0.0025")),  # 1-2年
    (999999, Decimal("0")),    # > 2年
]

# 红利税（按持有期）：<1月 20%, 1月-1年 10%, >1年 免
DIVIDEND_TAX_SCHEDULE = [
    (30, Decimal("0.20")),     # < 1个月
    (365, Decimal("0.10")),    # 1个月-1年
    (999999, Decimal("0")),    # > 1年
]


def _get_redemption_fee(holding_days: int) -> Decimal:
    """Get fund redemption fee rate based on holding period."""
    for days, rate in REDEMPTION_FEE_SCHEDULE:
        if holding_days < days:
            return rate
    return Decimal("0")


def _get_dividend_tax(holding_days: int) -> Decimal:
    """Get dividend withholding tax rate based on holding period."""
    for days, rate in DIVIDEND_TAX_SCHEDULE:
        if holding_days < days:
            return rate
    return Decimal("0")


def _calc_holding_days(purchase_date: datetime | None) -> int:
    """Calculate days since purchase."""
    if purchase_date is None:
        return 365  # 默认按1年算（保守）
    return (datetime.utcnow() - purchase_date).days


def _compute_trade_costs(
    action: str,
    amount: Decimal,
    asset_type: str,
    holding_days: int = 365,
) -> TradeCostDetail:
    """Compute detailed trading costs for a rebalance action.

    Args:
        action: "买入" or "卖出"
        amount: trade amount in CNY
        asset_type: "股票", "基金", "债券", "现金", "其他"
        holding_days: days held (for sell-side tax calculations)
    """
    stamp_tax = Decimal("0")
    commission = Decimal("0")
    redemption_fee = Decimal("0")
    dividend_tax = Decimal("0")

    if asset_type == "股票":
        # 买入：佣金
        # 卖出：佣金 + 印花税
        commission = max(amount * COMMISSION_RATE, COMMISSION_MIN)
        if action == "卖出":
            stamp_tax = amount * STAMP_TAX_RATE
            # 如果持有期<1年，红利税影响估算（简化：按金额的0.5%估算分红）
            div_tax_rate = _get_dividend_tax(holding_days)
            if div_tax_rate > 0:
                # 估算：假设年化分红率1.5%，按持有天数折算
                est_dividend = amount * Decimal("0.015") * min(holding_days, 365) / 365
                dividend_tax = est_dividend * div_tax_rate

    elif asset_type == "基金":
        # 买入：申购费（简化按0计入，大部分平台打折后为0）
        # 卖出：赎回费
        commission = max(amount * COMMISSION_RATE, COMMISSION_MIN)
        if action == "卖出":
            redemption_fee = amount * _get_redemption_fee(holding_days)

    elif asset_type == "债券":
        # 债券交易佣金较低
        commission = max(amount * Decimal("0.0001"), COMMISSION_MIN)

    # 现金/其他：无交易成本
    total_cost = stamp_tax + commission + redemption_fee + dividend_tax

    return TradeCostDetail(
        stamp_tax=stamp_tax.quantize(Decimal("0.01")),
        commission=commission.quantize(Decimal("0.01")),
        redemption_fee=redemption_fee.quantize(Decimal("0.01")),
        dividend_tax=dividend_tax.quantize(Decimal("0.01")),
        total_cost=total_cost.quantize(Decimal("0.01")),
    )


async def get_rebalance_suggestion(
    db: AsyncSession,
    deviation_threshold: float = 10.0,
) -> RebalanceResult:
    """Generate tax-aware rebalance suggestions.

    Only recommends rebalancing when:
    1. Deviation exceeds threshold (default 10%)
    2. After deducting trading costs, net benefit is positive

    Args:
        db: database session
        deviation_threshold: minimum deviation % to trigger rebalance alert
    """
    # Load targets
    t_result = await db.execute(
        select(AllocationTarget).order_by(AllocationTarget.asset_type)
    )
    targets = list(t_result.scalars().all())

    if not targets:
        return RebalanceResult(
            has_targets=False,
            deviation_threshold=deviation_threshold,
            suggestions=[],
            total_cost=Decimal("0"),
            total_net_benefit=Decimal("0"),
        )

    # Load holdings
    h_result = await db.execute(select(Holding))
    holdings = h_result.scalars().all()

    # Calculate current allocation by asset_type
    from collections import defaultdict

    type_values: dict[str, Decimal] = defaultdict(Decimal)
    type_holdings: dict[str, list[Holding]] = defaultdict(list)
    total = Decimal("0")

    for h in holdings:
        value = (
            h.quantity * h.latest_price
            if h.latest_price is not None
            else h.quantity * h.cost_price
        )
        type_values[h.asset_type] += value
        type_holdings[h.asset_type].append(h)
        total += value

    suggestions: list[RebalanceSuggestion] = []
    total_cost = Decimal("0")
    total_net_benefit = Decimal("0")

    for t in targets:
        actual_value = type_values.get(t.asset_type, Decimal("0"))
        actual_pct = float(actual_value / total * 100) if total > 0 else 0.0
        target_pct = float(t.target_ratio)
        deviation = actual_pct - target_pct

        if abs(deviation) <= deviation_threshold:
            # Within threshold — hold
            suggestions.append(
                RebalanceSuggestion(
                    asset_type=t.asset_type,
                    action="持有",
                    adjust_amount=Decimal("0"),
                    cost_detail=TradeCostDetail(
                        stamp_tax=Decimal("0"),
                        commission=Decimal("0"),
                        redemption_fee=Decimal("0"),
                        dividend_tax=Decimal("0"),
                        total_cost=Decimal("0"),
                    ),
                    net_benefit=Decimal("0"),
                    is_recommended=True,
                )
            )
            continue

        # Calculate adjustment amount
        target_value = total * Decimal(str(target_pct)) / 100
        diff = target_value - actual_value

        if diff > 0:
            action = "买入"
            adjust_amount = diff
        else:
            action = "卖出"
            adjust_amount = abs(diff)

        # Estimate average holding days for sell actions
        avg_holding_days = 365
        if action == "卖出" and t.asset_type in type_holdings:
            days_list = [
                _calc_holding_days(h.purchase_date)
                for h in type_holdings[t.asset_type]
                if h.purchase_date is not None
            ]
            if days_list:
                avg_holding_days = sum(days_list) // len(days_list)

        # Compute trade costs
        cost_detail = _compute_trade_costs(
            action=action,
            amount=adjust_amount,
            asset_type=t.asset_type,
            holding_days=avg_holding_days,
        )

        # Net benefit: the expected improvement from rebalancing
        # Simplified: benefit ≈ deviation% × adjust_amount / 100
        # (bringing allocation back to target reduces risk)
        estimated_benefit = abs(Decimal(str(deviation))) * adjust_amount / 100
        net_benefit = estimated_benefit - cost_detail.total_cost

        is_recommended = net_benefit > 0

        suggestions.append(
            RebalanceSuggestion(
                asset_type=t.asset_type,
                action=action,
                adjust_amount=adjust_amount.quantize(Decimal("0.01")),
                cost_detail=cost_detail,
                net_benefit=net_benefit.quantize(Decimal("0.01")),
                is_recommended=is_recommended,
            )
        )

        total_cost += cost_detail.total_cost
        total_net_benefit += net_benefit

    return RebalanceResult(
        has_targets=True,
        deviation_threshold=deviation_threshold,
        suggestions=suggestions,
        total_cost=total_cost.quantize(Decimal("0.01")),
        total_net_benefit=total_net_benefit.quantize(Decimal("0.01")),
    )
