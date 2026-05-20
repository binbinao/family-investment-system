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


# ---------------------------------------------------------------------------
# Correlation Matrix (#3)
# ---------------------------------------------------------------------------


class CorrelationPair(BaseModel):
    symbol_a: str
    name_a: str
    symbol_b: str
    name_b: str
    correlation: float  # Pearson correlation coefficient
    is_alert: bool      # |correlation| > 0.7


class DiversificationScore(BaseModel):
    score: float            # 0-100, higher = better diversified
    label: str              # 优秀/良好/一般/较差
    avg_correlation: float  # weighted average absolute correlation


class CorrelationMatrix(BaseModel):
    symbols: list[str]
    symbol_names: list[str]
    matrix: list[list[float]]
    pairs: list[CorrelationPair]
    diversification_score: DiversificationScore
    risk_contributions: list[dict]
    period_days: int


# ---------------------------------------------------------------------------
# Tax-Aware Rebalance (#1)
# ---------------------------------------------------------------------------


class TradeCostDetail(BaseModel):
    stamp_tax: Decimal       # 印花税 (卖出时0.05%)
    commission: Decimal      # 佣金 (买卖双向0.025%)
    redemption_fee: Decimal  # 赎回费 (基金持有期递减)
    dividend_tax: Decimal    # 红利税 (持有期相关)
    total_cost: Decimal      # 交易成本合计


class RebalanceSuggestion(BaseModel):
    asset_type: str
    action: str              # "买入" / "卖出" / "持有"
    adjust_amount: Decimal   # 建议调仓金额
    cost_detail: TradeCostDetail
    net_benefit: Decimal     # 税后净收益
    is_recommended: bool     # 税后净收益>0 才推荐


class RebalanceResult(BaseModel):
    has_targets: bool
    deviation_threshold: float   # 偏离阈值(%)
    suggestions: list[RebalanceSuggestion]
    total_cost: Decimal          # 总交易成本
    total_net_benefit: Decimal   # 总净收益
