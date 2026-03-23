import secrets
import uuid
from datetime import timedelta

import redis.asyncio as redis
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def generate_session_id() -> str:
    return secrets.token_urlsafe(64)


SESSION_PREFIX = "session:"


async def create_session(
    redis_client: redis.Redis, user_id: uuid.UUID
) -> str:
    session_id = generate_session_id()
    ttl = timedelta(hours=settings.SESSION_EXPIRE_HOURS)
    await redis_client.setex(
        f"{SESSION_PREFIX}{session_id}",
        int(ttl.total_seconds()),
        str(user_id),
    )
    return session_id


async def get_session_user_id(
    redis_client: redis.Redis, session_id: str
) -> str | None:
    user_id = await redis_client.get(f"{SESSION_PREFIX}{session_id}")
    return user_id


async def delete_session(
    redis_client: redis.Redis, session_id: str
) -> None:
    await redis_client.delete(f"{SESSION_PREFIX}{session_id}")
