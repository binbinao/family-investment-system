import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
class TestAuth:
    async def test_login_success(self, client: AsyncClient, test_user: User):
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert "session_id" in response.cookies

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrong"},
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "test"},
        )
        assert response.status_code == 401

    async def test_get_me(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        assert response.json()["username"] == "testuser"

    async def test_get_me_unauthorized(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_logout(self, authenticated_client: AsyncClient):
        response = await authenticated_client.post("/api/v1/auth/logout")
        assert response.status_code == 200
