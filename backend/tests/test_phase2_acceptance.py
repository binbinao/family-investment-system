"""
Task 1（自动化）：对照 Phase 2 设计 §2、§4 的 API 完成标准验收。
"""

import io
from decimal import Decimal
import openpyxl
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_import_template_holdings_public_xlsx(authenticated_client: AsyncClient):
    """模板下载无需登录（与 api 实现一致）；用已登录客户端亦可。"""
    r = await authenticated_client.get("/api/v1/import/template/holdings")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert len(r.content) > 100


@pytest.mark.asyncio
async def test_import_template_transactions_xlsx(authenticated_client: AsyncClient):
    r = await authenticated_client.get("/api/v1/import/template/transactions")
    assert r.status_code == 200
    assert len(r.content) > 80


@pytest.mark.asyncio
async def test_market_status_and_refresh_no_network(
    authenticated_client: AsyncClient, monkeypatch
):
    """无持仓时刷新不触网；有 A 股持仓时 mock 行情接口。"""
    st = await authenticated_client.get("/api/v1/market/status")
    assert st.status_code == 200
    assert isinstance(st.json(), list)

    empty = await authenticated_client.post("/api/v1/market/refresh")
    assert empty.status_code == 200
    body = empty.json()
    assert body["total"] == 0
    assert body["skipped"] == 0

    await authenticated_client.post(
        "/api/v1/holdings",
        json={
            "symbol": "688001",
            "name": "华兴源创",
            "asset_type": "股票",
            "quantity": 10,
            "cost_price": 30.0,
            "latest_price": 30.0,
        },
    )

    monkeypatch.setattr(
        "app.services.market._fetch_stock_price_sync",
        lambda symbol: {
            "latest_price": Decimal("31.5"),
            "price_change": Decimal("1.5"),
            "price_change_pct": Decimal("5"),
            "name": "华兴源创",
            "source": "akshare",
        },
    )

    class _FakeRedis:
        def __init__(self):
            self.store = {}

        async def get(self, key):
            return self.store.get(key)

        async def setex(self, key, ttl, value):
            self.store[key] = value

        async def delete(self, key):
            self.store.pop(key, None)

    fake = _FakeRedis()
    monkeypatch.setattr("app.services.market.get_redis", lambda: fake)

    ref = await authenticated_client.post("/api/v1/market/refresh")
    assert ref.status_code == 200
    assert ref.json()["success"] >= 1

    st2 = await authenticated_client.get("/api/v1/market/status")
    rows = st2.json()
    assert len(rows) >= 1
    sym = next(x for x in rows if x["symbol"] == "688001")
    assert sym["fail_count"] == 0
    assert "updated_at" in sym


@pytest.mark.asyncio
async def test_excel_import_holdings_success_and_row_error(
    authenticated_client: AsyncClient,
):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "持仓导入"
    ws.append(
        ["标识代码", "名称", "资产类型", "数量", "单位成本", "最新价(可选)", "账户(可选)"]
    )
    ws.append(
        ["IMP-OK-1", "验收测试标的", "股票", 10, 100.0, 101.0, ""]
    )
    ws.append(["BAD", "坏行", "不是有效类型", 1, 1.0, "", ""])

    buf = io.BytesIO()
    wb.save(buf)
    files = {"file": ("t.xlsx", buf.getvalue(), "application/octet-stream")}
    r = await authenticated_client.post("/api/v1/import/holdings", files=files)
    assert r.status_code == 200
    data = r.json()
    assert len(data["success"]) == 1
    assert data["success"][0]["symbol"] == "IMP-OK-1"
    assert len(data["errors"]) == 1
    assert data["errors"][0]["row"] == 3

    listed = await authenticated_client.get("/api/v1/holdings")
    symbols = {h["symbol"] for h in listed.json()}
    assert "IMP-OK-1" in symbols
