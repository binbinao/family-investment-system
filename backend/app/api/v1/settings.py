from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.setting import Setting
from app.models.user import User

router = APIRouter()


class SettingUpdate(BaseModel):
    key: str
    value: str


class SettingsBatch(BaseModel):
    settings: list[SettingUpdate]


@router.get("")
async def list_settings(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Setting))
    items = result.scalars().all()
    return {s.key: s.value for s in items}


@router.put("")
async def update_settings(
    data: SettingsBatch,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    for item in data.settings:
        result = await db.execute(
            select(Setting).where(Setting.key == item.key)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.value = item.value
        else:
            db.add(Setting(key=item.key, value=item.value))

    await db.commit()
    return {"success": True}
