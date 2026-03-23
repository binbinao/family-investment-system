import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHoldings:
    async def test_list_holdings_empty(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get("/api/v1/holdings")
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_holding(self, authenticated_client: AsyncClient):
        response = await authenticated_client.post(
            "/api/v1/holdings",
            json={
                "symbol": "600519",
                "name": "贵州茅台",
                "asset_type": "股票",
                "quantity": 100,
                "cost_price": 1800.00,
                "latest_price": 1900.00,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "600519"
        assert data["name"] == "贵州茅台"
        assert float(data["quantity"]) == 100
        assert data["market_value"] is not None

    async def test_update_holding(self, authenticated_client: AsyncClient):
        create_resp = await authenticated_client.post(
            "/api/v1/holdings",
            json={
                "symbol": "000001",
                "name": "平安银行",
                "asset_type": "股票",
                "quantity": 500,
                "cost_price": 12.50,
            },
        )
        holding_id = create_resp.json()["id"]

        update_resp = await authenticated_client.put(
            f"/api/v1/holdings/{holding_id}",
            json={"name": "平安银行A"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "平安银行A"

    async def test_update_price(self, authenticated_client: AsyncClient):
        create_resp = await authenticated_client.post(
            "/api/v1/holdings",
            json={
                "symbol": "005827",
                "name": "易方达蓝筹精选",
                "asset_type": "基金",
                "quantity": 1000,
                "cost_price": 2.50,
            },
        )
        holding_id = create_resp.json()["id"]

        price_resp = await authenticated_client.patch(
            f"/api/v1/holdings/{holding_id}/price",
            json={"latest_price": 2.80},
        )
        assert price_resp.status_code == 200
        assert float(price_resp.json()["latest_price"]) == 2.80
        assert price_resp.json()["profit_loss"] is not None

    async def test_delete_holding(self, authenticated_client: AsyncClient):
        create_resp = await authenticated_client.post(
            "/api/v1/holdings",
            json={
                "symbol": "510300",
                "name": "沪深300ETF",
                "asset_type": "基金",
                "quantity": 2000,
                "cost_price": 4.00,
            },
        )
        holding_id = create_resp.json()["id"]

        delete_resp = await authenticated_client.delete(
            f"/api/v1/holdings/{holding_id}"
        )
        assert delete_resp.status_code == 204

    async def test_profit_loss_calculation(self, authenticated_client: AsyncClient):
        resp = await authenticated_client.post(
            "/api/v1/holdings",
            json={
                "symbol": "601318",
                "name": "中国平安",
                "asset_type": "股票",
                "quantity": 200,
                "cost_price": 50.00,
                "latest_price": 55.00,
            },
        )
        data = resp.json()
        assert float(data["market_value"]) == 11000.00
        assert float(data["total_cost"]) == 10000.00
        assert float(data["profit_loss"]) == 1000.00
        assert abs(data["profit_loss_pct"] - 0.1) < 0.001

    async def test_unauthorized_access(self, client: AsyncClient):
        response = await client.get("/api/v1/holdings")
        assert response.status_code == 401
