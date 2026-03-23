from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.allocation import get_deviation, get_targets, update_targets

router = APIRouter()


class TargetItem(BaseModel):
    asset_type: str
    target_ratio: Decimal = Field(ge=0, le=100)


class TargetsUpdate(BaseModel):
    targets: list[TargetItem]


@router.get("/targets")
async def get_allocation_targets(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    targets = await get_targets(db)
    return [
        {
            "asset_type": t.asset_type,
            "target_ratio": t.target_ratio,
        }
        for t in targets
    ]


@router.put("/targets")
async def set_allocation_targets(
    data: TargetsUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    targets = await update_targets(
        db, [t.model_dump() for t in data.targets]
    )
    return [
        {
            "asset_type": t.asset_type,
            "target_ratio": t.target_ratio,
        }
        for t in targets
    ]


@router.get("/deviation")
async def get_allocation_deviation(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_deviation(db)
