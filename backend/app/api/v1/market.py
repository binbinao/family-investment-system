from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.market import get_market_status, refresh_all_prices

router = APIRouter()


@router.post("/refresh")
async def refresh_prices(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await refresh_all_prices(db, force=True)
    return result


@router.get("/status")
async def market_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_market_status(db)
