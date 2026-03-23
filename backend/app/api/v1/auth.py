from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.redis import get_redis
from app.core.security import create_session, delete_session
from app.models.user import User
from app.schemas.auth import LoginRequest, UserResponse
from app.services.auth import authenticate_user

router = APIRouter()


@router.post("/login", response_model=UserResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    redis_client = get_redis()
    session_id = await create_session(redis_client, user.id)

    response = JSONResponse(
        content=UserResponse.model_validate(user).model_dump(mode="json")
    )
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )
    return response


@router.post("/logout")
async def logout(session_id: str | None = Cookie(None)):
    if session_id:
        redis_client = get_redis()
        await delete_session(redis_client, session_id)

    response = JSONResponse(content={"detail": "已登出"})
    response.delete_cookie("session_id")
    return response


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user
