from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.holdings import router as holdings_router
from app.api.v1.transactions import router as transactions_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(holdings_router, prefix="/holdings", tags=["持仓"])
api_router.include_router(transactions_router, prefix="/transactions", tags=["交易"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["总览"])
