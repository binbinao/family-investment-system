import pytest
from httpx import AsyncClient


async def create_test_holding(client: AsyncClient) -> str:
    resp = await client.post(
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
    return resp.json()["id"]


@pytest.mark.asyncio
class TestTransactions:
    async def test_buy_updates_holding(self, authenticated_client: AsyncClient):
        holding_id = await create_test_holding(authenticated_client)

        resp = await authenticated_client.post(
            "/api/v1/transactions",
            json={
                "holding_id": holding_id,
                "type": "买入",
                "quantity": 50,
                "price": 1850.00,
                "date": "2026-03-20",
            },
        )
        assert resp.status_code == 201

        holdings_resp = await authenticated_client.get("/api/v1/holdings")
        holding = next(h for h in holdings_resp.json() if h["id"] == holding_id)
        assert float(holding["quantity"]) == 150

    async def test_sell_calculates_pnl(self, authenticated_client: AsyncClient):
        holding_id = await create_test_holding(authenticated_client)

        resp = await authenticated_client.post(
            "/api/v1/transactions",
            json={
                "holding_id": holding_id,
                "type": "卖出",
                "quantity": 30,
                "price": 2000.00,
                "fee": 10,
                "date": "2026-03-20",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["realized_pnl"] is not None
        assert float(data["realized_pnl"]) == (2000 - 1800) * 30 - 10

    async def test_sell_exceeds_quantity(self, authenticated_client: AsyncClient):
        holding_id = await create_test_holding(authenticated_client)

        resp = await authenticated_client.post(
            "/api/v1/transactions",
            json={
                "holding_id": holding_id,
                "type": "卖出",
                "quantity": 200,
                "price": 2000.00,
                "date": "2026-03-20",
            },
        )
        assert resp.status_code == 400

    async def test_dividend(self, authenticated_client: AsyncClient):
        holding_id = await create_test_holding(authenticated_client)

        resp = await authenticated_client.post(
            "/api/v1/transactions",
            json={
                "holding_id": holding_id,
                "type": "现金分红",
                "quantity": 100,
                "price": 5.00,
                "date": "2026-03-20",
            },
        )
        assert resp.status_code == 201
        assert float(resp.json()["realized_pnl"]) == 500.00

    async def test_reinvest(self, authenticated_client: AsyncClient):
        holding_id = await create_test_holding(authenticated_client)

        resp = await authenticated_client.post(
            "/api/v1/transactions",
            json={
                "holding_id": holding_id,
                "type": "红利再投资",
                "quantity": 10,
                "price": 1800.00,
                "date": "2026-03-20",
            },
        )
        assert resp.status_code == 201

        holdings_resp = await authenticated_client.get("/api/v1/holdings")
        holding = next(h for h in holdings_resp.json() if h["id"] == holding_id)
        assert float(holding["quantity"]) == 110

    async def test_list_transactions(self, authenticated_client: AsyncClient):
        holding_id = await create_test_holding(authenticated_client)

        await authenticated_client.post(
            "/api/v1/transactions",
            json={
                "holding_id": holding_id,
                "type": "买入",
                "quantity": 10,
                "price": 1850.00,
                "date": "2026-03-20",
            },
        )

        resp = await authenticated_client.get("/api/v1/transactions")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_filter_by_holding(self, authenticated_client: AsyncClient):
        holding_id = await create_test_holding(authenticated_client)

        await authenticated_client.post(
            "/api/v1/transactions",
            json={
                "holding_id": holding_id,
                "type": "买入",
                "quantity": 10,
                "price": 1850.00,
                "date": "2026-03-20",
            },
        )

        resp = await authenticated_client.get(
            f"/api/v1/transactions?holding_id={holding_id}"
        )
        assert resp.status_code == 200
        for t in resp.json():
            assert t["holding_id"] == holding_id
