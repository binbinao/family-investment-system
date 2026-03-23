from fastapi import APIRouter

from app.api.v1.allocation import router as allocation_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.holdings import router as holdings_router
from app.api.v1.imports import router as imports_router
from app.api.v1.market import router as market_router
from app.api.v1.snapshots import router as snapshots_router
from app.api.v1.transactions import router as transactions_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(holdings_router, prefix="/holdings", tags=["持仓"])
api_router.include_router(transactions_router, prefix="/transactions", tags=["交易"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["总览"])
api_router.include_router(market_router, prefix="/market", tags=["行情"])
api_router.include_router(imports_router, prefix="/import", tags=["导入"])
api_router.include_router(snapshots_router, prefix="/snapshots", tags=["快照"])
api_router.include_router(allocation_router, prefix="/allocation", tags=["配置"])
