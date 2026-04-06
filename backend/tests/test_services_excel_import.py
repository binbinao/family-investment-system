"""Task 4：Excel 导入服务层（不经过 HTTP）。"""

import io

import openpyxl
import pytest

from app.services.excel_import import create_holding_template, import_holdings


@pytest.mark.asyncio
async def test_import_holdings_from_bundled_template(db_session):
    content = create_holding_template()
    result = await import_holdings(db_session, content)
    assert len(result["success"]) >= 1
    assert not result["errors"]


@pytest.mark.asyncio
async def test_import_holdings_rejects_bad_quantity(db_session):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "持仓导入"
    ws.append(
        ["标识代码", "名称", "资产类型", "数量", "单位成本", "最新价(可选)", "账户(可选)"]
    )
    ws.append(["X-NEG", "负数量", "股票", -1, 1.0, "", ""])
    buf = io.BytesIO()
    wb.save(buf)
    result = await import_holdings(db_session, buf.getvalue())
    assert result["success"] == []
    assert len(result["errors"]) == 1
    assert "数量" in result["errors"][0]["error"]
