import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.holding import (
    HoldingCreate,
    HoldingPriceUpdate,
    HoldingResponse,
    HoldingUpdate,
)
from app.services.holding import (
    create_holding,
    delete_holding,
    list_holdings,
    update_holding,
    update_price,
)

router = APIRouter()


@router.get("", response_model=list[HoldingResponse])
async def get_holdings(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await list_holdings(db)


@router.post("", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
async def add_holding(
    data: HoldingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await create_holding(db, data, user.id)


@router.put("/{holding_id}", response_model=HoldingResponse)
async def edit_holding(
    holding_id: uuid.UUID,
    data: HoldingUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await update_holding(db, holding_id, data, user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="持仓不存在"
        )
    return result


@router.delete("/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_holding(
    holding_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    success = await delete_holding(db, holding_id, user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="持仓不存在"
        )


@router.patch("/{holding_id}/price", response_model=HoldingResponse)
async def set_price(
    holding_id: uuid.UUID,
    data: HoldingPriceUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await update_price(db, holding_id, data.latest_price, user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="持仓不存在"
        )
    return result
