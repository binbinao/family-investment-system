import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.memo import create_memo, delete_memo, list_memos

router = APIRouter()


class MemoCreate(BaseModel):
    content: str


@router.post("")
async def new_memo(
    data: MemoCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    memo = await create_memo(db, data.content, user.id)
    return {
        "id": str(memo.id),
        "content": memo.content,
        "related_symbols": memo.related_symbols,
        "user_id": str(memo.user_id),
        "created_at": memo.created_at.isoformat(),
    }


@router.get("")
async def memo_list(
    symbol: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    memos = await list_memos(db, symbol, limit)
    return [
        {
            "id": str(m.id),
            "content": m.content,
            "related_symbols": m.related_symbols,
            "user_id": str(m.user_id),
            "created_at": m.created_at.isoformat(),
        }
        for m in memos
    ]


@router.delete("/{memo_id}")
async def remove_memo(
    memo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ok = await delete_memo(db, memo_id)
    if not ok:
        raise HTTPException(status_code=404, detail="备忘录不存在")
    return {"success": True}
