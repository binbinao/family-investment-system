from decimal import Decimal

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_market_value: Decimal
    total_cost: Decimal
    total_profit_loss: Decimal
    total_profit_loss_pct: float
    holdings_count: int


class AllocationItem(BaseModel):
    asset_type: str
    market_value: Decimal
    percentage: float


class RiskMetrics(BaseModel):
    max_drawdown: float       # 最大回撤 (%)
    annualized_volatility: float  # 年化波动率 (%)
    sharpe_ratio: float       # 夏普比率
    var_95: float             # VaR 95% (%)
    period_days: int          # 计算周期(天)


class SectorAllocation(BaseModel):
    sector: str
    market_value: Decimal
    percentage: float
    holdings_count: int
