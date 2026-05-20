import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class HoldingCreate(BaseModel):
    symbol: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    asset_type: str = Field(..., pattern="^(股票|基金|债券|现金|其他)$")
    sector: str | None = Field(None, max_length=50, description="申万一级行业分类")
    quantity: Decimal = Field(..., gt=0)
    cost_price: Decimal = Field(..., gt=0)
    latest_price: Decimal | None = None
    purchase_date: datetime | None = Field(None, description="首次买入日期")
    cost_method: str = Field("fifo", pattern="^(fifo|average)$")
    account: str | None = Field(None, max_length=100)


class HoldingUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    quantity: Decimal | None = Field(None, gt=0)
    cost_price: Decimal | None = Field(None, gt=0)
    sector: str | None = Field(None, max_length=50, description="申万一级行业分类")
    account: str | None = Field(None, max_length=100)


class HoldingPriceUpdate(BaseModel):
    latest_price: Decimal = Field(..., ge=0)


class HoldingResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    name: str
    asset_type: str
    sector: str | None = None
    quantity: Decimal
    cost_price: Decimal
    latest_price: Decimal | None
    latest_price_updated_at: datetime | None
    purchase_date: datetime | None = None
    cost_method: str = "fifo"
    account: str | None
    market_value: Decimal | None = None
    total_cost: Decimal | None = None
    profit_loss: Decimal | None = None
    profit_loss_pct: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
