import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    holding_id: uuid.UUID
    type: str = Field(..., pattern="^(买入|卖出|现金分红|红利再投资)$")
    quantity: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., ge=0)
    fee: Decimal = Field(default=Decimal("0"), ge=0)
    date: date


class TransactionResponse(BaseModel):
    id: uuid.UUID
    holding_id: uuid.UUID
    symbol: str
    type: str
    quantity: Decimal
    price: Decimal
    fee: Decimal
    realized_pnl: Decimal | None
    date: date
    user_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
