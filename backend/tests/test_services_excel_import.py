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


def _build_initial_wb(holding_rows, target_rows):
    """构建双 sheet 初始建档工作簿（模拟用户填好的模板）。"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "持仓导入"
    ws.append(
        ["标识代码", "名称", "资产类型", "数量", "单位成本", "最新价(可选)", "账户(可选)"]
    )
    for row in holding_rows:
        ws.append(row)
    ws_t = wb.create_sheet("配置目标")
    ws_t.append(["资产类型", "目标比例(%)"])
    for row in target_rows:
        ws_t.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_import_initial_imports_holdings_and_targets(db_session):
    from sqlalchemy import select

    from app.models.allocation_target import AllocationTarget
    from app.services.excel_import import import_initial

    content = _build_initial_wb(
        [["600519", "贵州茅台", "股票", 100, 1800.00, 1850.00, ""]],
        [["股票", 40], ["基金", 30], ["现金", 20]],
    )
    result = await import_initial(db_session, content, user_id=None)

    assert len(result["success"]) == 1
    assert not result["errors"]
    assert result["targets"]["updated"] is True
    assert not result["targets"]["errors"]

    targets = (
        (await db_session.execute(select(AllocationTarget).order_by(AllocationTarget.asset_type)))
        .scalars()
        .all()
    )
    assert {(t.asset_type, str(t.target_ratio)) for t in targets} == {
        ("股票", "40.00"),
        ("基金", "30.00"),
        ("现金", "20.00"),
    }


@pytest.mark.asyncio
async def test_import_initial_rejects_invalid_target_rows(db_session):
    from app.services.excel_import import import_initial

    content = _build_initial_wb(
        [["600519", "贵州茅台", "股票", 100, 1800.00, "", ""]],
        [["股票", 40], ["黄金", 10], ["基金", 150], ["债券", "abc"]],
    )
    result = await import_initial(db_session, content, user_id=None)

    assert len(result["success"]) == 1  # 持仓仍导入
    assert result["targets"]["updated"] is False
    target_errors = result["targets"]["errors"]
    assert len(target_errors) == 3
    assert "资产类型无效" in target_errors[0]["error"]
    assert "比例" in target_errors[1]["error"]
    assert "比例格式错误" in target_errors[2]["error"]


@pytest.mark.asyncio
async def test_import_initial_bundled_template_round_trip(db_session):
    """生成的初始建档模板本身必须可直接导入成功。"""
    from app.services.excel_import import create_initial_template, import_initial

    content = create_initial_template()
    result = await import_initial(db_session, content, user_id=None)
    assert not result["errors"]
    assert not result["targets"]["errors"]
    assert len(result["success"]) >= 1
    assert result["targets"]["updated"] is True
