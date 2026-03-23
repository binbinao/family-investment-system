"""Initialize default users for the family investment system."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session, engine
from app.core.security import hash_password
from app.models import *  # noqa: F401, F403
from app.models.user import User


DEFAULT_USERS = [
    {"username": "admin", "password": "admin123", "display_name": "管理员"},
    {"username": "family1", "password": "family123", "display_name": "家人一"},
    {"username": "family2", "password": "family123", "display_name": "家人二"},
]


async def init_users():
    async with async_session() as session:
        for user_data in DEFAULT_USERS:
            result = await session.execute(
                select(User).where(User.username == user_data["username"])
            )
            existing = result.scalar_one_or_none()
            if existing:
                print(f"用户 {user_data['username']} 已存在，跳过")
                continue

            user = User(
                username=user_data["username"],
                password_hash=hash_password(user_data["password"]),
                display_name=user_data["display_name"],
            )
            session.add(user)
            print(f"创建用户: {user_data['username']}")

        await session.commit()
    print("用户初始化完成")


if __name__ == "__main__":
    asyncio.run(init_users())
