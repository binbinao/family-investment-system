from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.daily_report import generate_daily_report, get_latest_report, list_reports

router = APIRouter()


@router.get("/latest")
async def latest_report(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    report = await get_latest_report(db)
    if not report:
        return {"has_report": False}
    return {
        "has_report": True,
        "date": report.date.isoformat(),
        "summary": report.summary,
        "content_markdown": report.content_markdown,
    }


@router.get("")
async def report_list(
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    reports = await list_reports(db, limit)
    return [
        {
            "id": str(r.id),
            "date": r.date.isoformat(),
            "summary": r.summary,
            "content_markdown": r.content_markdown,
            "created_at": r.created_at.isoformat(),
        }
        for r in reports
    ]


@router.post("/generate")
async def trigger_report(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    report = await generate_daily_report(db)
    if not report:
        return {"success": False, "message": "晨报已存在或 AI 服务不可用"}
    return {
        "success": True,
        "date": report.date.isoformat(),
        "summary": report.summary,
    }
