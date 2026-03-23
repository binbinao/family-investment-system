from urllib.parse import quote

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.excel_import import (
    create_holding_template,
    create_transaction_template,
    import_holdings,
    import_transactions,
)

router = APIRouter()


@router.get("/template/{template_type}")
async def download_template(template_type: str):
    if template_type == "holdings":
        content = create_holding_template()
        filename = "持仓导入模板.xlsx"
    elif template_type == "transactions":
        content = create_transaction_template()
        filename = "交易导入模板.xlsx"
    else:
        return {"error": "无效的模板类型，请使用 holdings 或 transactions"}

    encoded_name = quote(filename)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"
        },
    )


@router.post("/holdings")
async def upload_holdings(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await file.read()
    result = await import_holdings(db, content)
    return result


@router.post("/transactions")
async def upload_transactions(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await file.read()
    result = await import_transactions(db, content, user.id)
    return result
