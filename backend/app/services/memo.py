"""Family memo service with symbol association."""

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memo import Memo


def _extract_symbols(content: str) -> str:
    """Extract stock/fund symbols from content (e.g. #600519)."""
    symbols = re.findall(r"#(\d{6})", content)
    return ",".join(set(symbols)) if symbols else ""


async def create_memo(
    db: AsyncSession, content: str, user_id: uuid.UUID
) -> Memo:
    related_symbols = _extract_symbols(content)
    memo = Memo(
        content=content,
        related_symbols=related_symbols or None,
        user_id=user_id,
    )
    db.add(memo)
    await db.commit()
    await db.refresh(memo)
    return memo


async def list_memos(
    db: AsyncSession,
    symbol: str | None = None,
    limit: int = 50,
) -> list[Memo]:
    query = select(Memo).order_by(Memo.created_at.desc()).limit(limit)
    if symbol:
        query = query.where(Memo.related_symbols.contains(symbol))
    result = await db.execute(query)
    return list(result.scalars().all())


async def delete_memo(db: AsyncSession, memo_id: uuid.UUID) -> bool:
    result = await db.execute(select(Memo).where(Memo.id == memo_id))
    memo = result.scalar_one_or_none()
    if not memo:
        return False
    await db.delete(memo)
    await db.commit()
    return True
