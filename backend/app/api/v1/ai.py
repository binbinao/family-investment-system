from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.ai import (
    deep_analysis_stream,
    get_conversation_history,
    quick_chat_stream,
)

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    mode: str = "quick"  # quick or deep


@router.post("/chat")
async def ai_chat(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if req.mode == "deep":
        generator = deep_analysis_stream(db, user.id, req.question)
    else:
        generator = quick_chat_stream(db, user.id, req.question)

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history")
async def ai_history(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversations = await get_conversation_history(db, user.id, limit)
    return [
        {
            "id": str(c.id),
            "mode": c.mode,
            "question": c.question,
            "answer": c.answer,
            "created_at": c.created_at.isoformat(),
        }
        for c in conversations
    ]
