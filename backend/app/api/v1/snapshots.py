from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.snapshot import build_last_30_days_chart, list_snapshots

router = APIRouter()


@router.get("/chart")
async def get_snapshots_chart(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """近 30 日走势：合并真实快照与基于当前持仓的缺失日模拟。"""
    return await build_last_30_days_chart(db)


@router.get("")
async def get_snapshots(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    snapshots = await list_snapshots(db, start_date, end_date)
    return [
        {
            "date": s.date.isoformat(),
            "total_market_value": s.total_market_value,
            "total_cost": s.total_cost,
            "total_profit_loss": s.total_profit_loss,
        }
        for s in snapshots
    ]
