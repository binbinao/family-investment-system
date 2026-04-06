import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_deviation_alert_over_10_percent(authenticated_client: AsyncClient):
    await authenticated_client.put(
        "/api/v1/allocation/targets",
        json={"targets": [{"asset_type": "股票", "target_ratio": 50}]},
    )
    await authenticated_client.post(
        "/api/v1/holdings",
        json={
            "symbol": "600519",
            "name": "贵州茅台",
            "asset_type": "股票",
            "quantity": 100,
            "cost_price": 100,
            "latest_price": 100,
        },
    )
    r = await authenticated_client.get("/api/v1/allocation/deviation")
    assert r.status_code == 200
    data = r.json()
    assert data.get("has_targets") is True
    assert data.get("has_alert") is True


@pytest.mark.asyncio
async def test_allocation_targets_round_trip(authenticated_client: AsyncClient):
    put = await authenticated_client.put(
        "/api/v1/allocation/targets",
        json={
            "targets": [
                {"asset_type": "股票", "target_ratio": 40},
                {"asset_type": "基金", "target_ratio": 60},
            ]
        },
    )
    assert put.status_code == 200
    got = await authenticated_client.get("/api/v1/allocation/targets")
    assert got.status_code == 200
    body = got.json()
    types = {x["asset_type"]: float(x["target_ratio"]) for x in body}
    assert types.get("股票") == 40.0
    assert types.get("基金") == 60.0
