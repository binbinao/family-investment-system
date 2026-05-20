from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.dashboard import (
    AllocationItem,
    DashboardSummary,
    RiskMetrics,
    SectorAllocation,
)
from app.services.dashboard import (
    get_allocation,
    get_risk_metrics,
    get_sector_allocation,
    get_summary,
)

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_summary(db)


@router.get("/allocation", response_model=list[AllocationItem])
async def dashboard_allocation(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_allocation(db)


@router.get("/risk-metrics", response_model=RiskMetrics | None)
async def dashboard_risk_metrics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Portfolio risk metrics: max drawdown, Sharpe, volatility, VaR."""
    return await get_risk_metrics(db)


@router.get("/sector-allocation", response_model=list[SectorAllocation])
async def dashboard_sector_allocation(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Allocation by sector (申万一级行业)."""
    return await get_sector_allocation(db)
