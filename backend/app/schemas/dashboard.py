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
