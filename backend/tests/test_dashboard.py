import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestDashboard:
    async def test_summary_empty(self, authenticated_client: AsyncClient):
        resp = await authenticated_client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["total_market_value"]) == 0
        assert data["holdings_count"] == 0

    async def test_summary_with_holdings(self, authenticated_client: AsyncClient):
        await authenticated_client.post(
            "/api/v1/holdings",
            json={
                "symbol": "600519",
                "name": "贵州茅台",
                "asset_type": "股票",
                "quantity": 100,
                "cost_price": 1800.00,
                "latest_price": 2000.00,
            },
        )
        await authenticated_client.post(
            "/api/v1/holdings",
            json={
                "symbol": "005827",
                "name": "易方达蓝筹",
                "asset_type": "基金",
                "quantity": 1000,
                "cost_price": 2.50,
                "latest_price": 2.80,
            },
        )

        resp = await authenticated_client.get("/api/v1/dashboard/summary")
        data = resp.json()
        assert data["holdings_count"] == 2
        assert float(data["total_market_value"]) == 200000 + 2800
        assert float(data["total_cost"]) == 180000 + 2500
        assert float(data["total_profit_loss"]) == 20300

    async def test_allocation(self, authenticated_client: AsyncClient):
        await authenticated_client.post(
            "/api/v1/holdings",
            json={
                "symbol": "600519",
                "name": "贵州茅台",
                "asset_type": "股票",
                "quantity": 100,
                "cost_price": 1800.00,
                "latest_price": 2000.00,
            },
        )
        await authenticated_client.post(
            "/api/v1/holdings",
            json={
                "symbol": "005827",
                "name": "易方达蓝筹",
                "asset_type": "基金",
                "quantity": 1000,
                "cost_price": 2.50,
                "latest_price": 2.80,
            },
        )

        resp = await authenticated_client.get("/api/v1/dashboard/allocation")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

        total_pct = sum(item["percentage"] for item in data)
        assert abs(total_pct - 100.0) < 0.1

    async def test_unauthorized(self, client: AsyncClient):
        resp = await client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 401
