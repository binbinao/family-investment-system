import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.transaction import create_transaction, list_transactions

router = APIRouter()


@router.get("", response_model=list[TransactionResponse])
async def get_transactions(
    holding_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await list_transactions(db, holding_id)


@router.post("", response_model=TransactionResponse, status_code=201)
async def add_transaction(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await create_transaction(db, data, user.id)
