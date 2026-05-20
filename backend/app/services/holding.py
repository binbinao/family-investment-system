import json
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holding import Holding
from app.models.operation_log import OperationLog
from app.schemas.holding import HoldingCreate, HoldingResponse, HoldingUpdate


def _enrich_holding(h: Holding) -> HoldingResponse:
    market_value = None
    total_cost = h.quantity * h.cost_price
    profit_loss = None
    profit_loss_pct = None

    if h.latest_price is not None:
        market_value = h.quantity * h.latest_price
        profit_loss = market_value - total_cost
        if total_cost > 0:
            profit_loss_pct = float(profit_loss / total_cost)

    return HoldingResponse(
        id=h.id,
        symbol=h.symbol,
        name=h.name,
        asset_type=h.asset_type,
        sector=h.sector,
        quantity=h.quantity,
        cost_price=h.cost_price,
        latest_price=h.latest_price,
        latest_price_updated_at=h.latest_price_updated_at,
        purchase_date=h.purchase_date,
        cost_method=h.cost_method or "fifo",
        account=h.account,
        market_value=market_value,
        total_cost=total_cost,
        profit_loss=profit_loss,
        profit_loss_pct=profit_loss_pct,
        created_at=h.created_at,
        updated_at=h.updated_at,
    )


async def list_holdings(db: AsyncSession) -> list[HoldingResponse]:
    result = await db.execute(select(Holding).order_by(Holding.created_at))
    holdings = result.scalars().all()
    return [_enrich_holding(h) for h in holdings]


async def get_holding(db: AsyncSession, holding_id: uuid.UUID) -> Holding | None:
    result = await db.execute(select(Holding).where(Holding.id == holding_id))
    return result.scalar_one_or_none()


async def create_holding(
    db: AsyncSession, data: HoldingCreate, user_id: uuid.UUID
) -> HoldingResponse:
    holding = Holding(
        symbol=data.symbol,
        name=data.name,
        asset_type=data.asset_type,
        sector=data.sector,
        quantity=data.quantity,
        cost_price=data.cost_price,
        latest_price=data.latest_price,
        latest_price_updated_at=datetime.utcnow() if data.latest_price else None,
        purchase_date=data.purchase_date,
        cost_method=data.cost_method,
        account=data.account,
    )
    db.add(holding)

    log = OperationLog(
        user_id=user_id,
        action="添加持仓",
        detail=json.dumps(
            {"symbol": data.symbol, "name": data.name, "quantity": str(data.quantity)},
            ensure_ascii=False,
        ),
    )
    db.add(log)

    await db.commit()
    await db.refresh(holding)
    return _enrich_holding(holding)


async def update_holding(
    db: AsyncSession,
    holding_id: uuid.UUID,
    data: HoldingUpdate,
    user_id: uuid.UUID,
) -> HoldingResponse | None:
    holding = await get_holding(db, holding_id)
    if not holding:
        return None

    changes = {}
    if data.name is not None:
        holding.name = data.name
        changes["name"] = data.name
    if data.quantity is not None:
        holding.quantity = data.quantity
        changes["quantity"] = str(data.quantity)
    if data.cost_price is not None:
        holding.cost_price = data.cost_price
        changes["cost_price"] = str(data.cost_price)
    if data.account is not None:
        holding.account = data.account
        changes["account"] = data.account
    if data.sector is not None:
        holding.sector = data.sector
        changes["sector"] = data.sector

    holding.updated_at = datetime.utcnow()

    log = OperationLog(
        user_id=user_id,
        action="编辑持仓",
        detail=json.dumps(
            {"symbol": holding.symbol, "changes": changes}, ensure_ascii=False
        ),
    )
    db.add(log)

    await db.commit()
    await db.refresh(holding)
    return _enrich_holding(holding)


async def delete_holding(
    db: AsyncSession, holding_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    holding = await get_holding(db, holding_id)
    if not holding:
        return False

    log = OperationLog(
        user_id=user_id,
        action="删除持仓",
        detail=json.dumps(
            {"symbol": holding.symbol, "name": holding.name}, ensure_ascii=False
        ),
    )
    db.add(log)

    await db.delete(holding)
    await db.commit()
    return True


async def update_price(
    db: AsyncSession,
    holding_id: uuid.UUID,
    latest_price: Decimal,
    user_id: uuid.UUID,
) -> HoldingResponse | None:
    holding = await get_holding(db, holding_id)
    if not holding:
        return None

    holding.latest_price = latest_price
    holding.latest_price_updated_at = datetime.utcnow()
    holding.updated_at = datetime.utcnow()

    log = OperationLog(
        user_id=user_id,
        action="更新价格",
        detail=json.dumps(
            {"symbol": holding.symbol, "latest_price": str(latest_price)},
            ensure_ascii=False,
        ),
    )
    db.add(log)

    await db.commit()
    await db.refresh(holding)
    return _enrich_holding(holding)
