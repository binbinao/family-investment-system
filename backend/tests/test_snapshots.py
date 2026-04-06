import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_snapshots_list_empty(authenticated_client: AsyncClient):
    r = await authenticated_client.get("/api/v1/snapshots")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_snapshots_chart_empty_without_holdings(authenticated_client: AsyncClient):
    r = await authenticated_client.get("/api/v1/snapshots/chart")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_snapshots_date_filter(authenticated_client: AsyncClient):
    r = await authenticated_client.get(
        "/api/v1/snapshots",
        params={"start_date": "2026-01-01", "end_date": "2026-12-31"},
    )
    assert r.status_code == 200
    assert r.json() == []
