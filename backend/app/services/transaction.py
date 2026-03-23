import json
import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holding import Holding
from app.models.operation_log import OperationLog
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionResponse


async def list_transactions(
    db: AsyncSession, holding_id: uuid.UUID | None = None
) -> list[TransactionResponse]:
    query = select(Transaction).order_by(Transaction.date.desc(), Transaction.created_at.desc())
    if holding_id:
        query = query.where(Transaction.holding_id == holding_id)

    result = await db.execute(query)
    return [TransactionResponse.model_validate(t) for t in result.scalars().all()]


async def create_transaction(
    db: AsyncSession, data: TransactionCreate, user_id: uuid.UUID
) -> TransactionResponse:
    result = await db.execute(
        select(Holding).where(Holding.id == data.holding_id)
    )
    holding = result.scalar_one_or_none()
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="持仓不存在",
        )

    realized_pnl = None

    if data.type == "买入":
        new_quantity = holding.quantity + data.quantity
        new_cost = (
            holding.quantity * holding.cost_price + data.quantity * data.price
        ) / new_quantity
        holding.quantity = new_quantity
        holding.cost_price = new_cost

    elif data.type == "卖出":
        if data.quantity > holding.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"卖出数量({data.quantity})超过持仓数量({holding.quantity})",
            )
        realized_pnl = (data.price - holding.cost_price) * data.quantity - data.fee
        holding.quantity = holding.quantity - data.quantity

    elif data.type == "现金分红":
        realized_pnl = data.quantity * data.price

    elif data.type == "红利再投资":
        new_quantity = holding.quantity + data.quantity
        holding.cost_price = (
            holding.quantity * holding.cost_price
        ) / new_quantity
        holding.quantity = new_quantity

    transaction = Transaction(
        holding_id=data.holding_id,
        symbol=holding.symbol,
        type=data.type,
        quantity=data.quantity,
        price=data.price,
        fee=data.fee,
        realized_pnl=realized_pnl,
        date=data.date,
        user_id=user_id,
    )
    db.add(transaction)

    log = OperationLog(
        user_id=user_id,
        action="记录交易",
        detail=json.dumps(
            {
                "symbol": holding.symbol,
                "type": data.type,
                "quantity": str(data.quantity),
                "price": str(data.price),
            },
            ensure_ascii=False,
        ),
    )
    db.add(log)

    await db.commit()
    await db.refresh(transaction)
    return TransactionResponse.model_validate(transaction)
