"""Excel import service for holdings and transactions."""

import io
import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from openpyxl import Workbook, load_workbook
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holding import Holding
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)

HOLDING_COLUMNS = ["标的代码", "标的名称", "资产类型", "数量", "成本价", "账户"]
HOLDING_REQUIRED = {"标的代码", "标的名称", "资产类型", "数量", "成本价"}

TRANSACTION_COLUMNS = ["标的代码", "交易类型", "数量", "价格", "日期", "手续费", "账户"]
TRANSACTION_REQUIRED = {"标的代码", "交易类型", "数量", "价格", "日期"}

VALID_ASSET_TYPES = {"股票", "基金", "债券", "现金", "其他"}
VALID_TX_TYPES = {"买入", "卖出", "现金分红", "红利再投资"}


def create_holding_template() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "持仓导入"
    ws.append(HOLDING_COLUMNS)
    ws.append(["600519", "贵州茅台", "股票", 100, 1800.00, "张三-华泰"])
    ws.append(["005827", "易方达蓝筹精选", "基金", 5000, 2.50, ""])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def create_transaction_template() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "交易导入"
    ws.append(TRANSACTION_COLUMNS)
    ws.append(["600519", "买入", 100, 1800.00, "2026-01-15", 5.00, "张三-华泰"])
    ws.append(["600519", "卖出", 50, 2000.00, "2026-03-20", 10.00, ""])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _parse_decimal(value, field_name: str) -> tuple[Decimal | None, str | None]:
    if value is None:
        return None, f"{field_name}不能为空"
    try:
        d = Decimal(str(value))
        if d <= 0:
            return None, f"{field_name}必须大于0"
        return d, None
    except (InvalidOperation, ValueError):
        return None, f"{field_name}格式错误: {value}"


def _parse_date(value) -> tuple[date | None, str | None]:
    if value is None:
        return None, "日期不能为空"
    if isinstance(value, datetime):
        return value.date(), None
    if isinstance(value, date):
        return value, None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date(), None
    except ValueError:
        return None, f"日期格式错误: {value}（应为 YYYY-MM-DD）"


async def import_holdings(
    db: AsyncSession, file_content: bytes
) -> dict:
    """Import holdings from Excel. Returns success/error summary."""
    wb = load_workbook(io.BytesIO(file_content), data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(min_row=2, values_only=True))
    results = {"success": [], "errors": []}

    for i, row in enumerate(rows, start=2):
        if len(row) < 5:
            results["errors"].append({"row": i, "error": "列数不足"})
            continue

        symbol = str(row[0]).strip() if row[0] else None
        name = str(row[1]).strip() if row[1] else None
        asset_type = str(row[2]).strip() if row[2] else None
        account = str(row[5]).strip() if len(row) > 5 and row[5] else None

        errors = []
        if not symbol:
            errors.append("标的代码不能为空")
        if not name:
            errors.append("标的名称不能为空")
        if asset_type not in VALID_ASSET_TYPES:
            errors.append(f"资产类型无效: {asset_type}")

        quantity, err = _parse_decimal(row[3], "数量")
        if err:
            errors.append(err)
        cost_price, err = _parse_decimal(row[4], "成本价")
        if err:
            errors.append(err)

        if errors:
            results["errors"].append({"row": i, "error": "; ".join(errors)})
            continue

        holding = Holding(
            symbol=symbol,
            name=name,
            asset_type=asset_type,
            quantity=quantity,
            cost_price=cost_price,
            account=account,
        )
        db.add(holding)
        results["success"].append({"row": i, "symbol": symbol, "name": name})

    if results["success"]:
        await db.commit()

    return results


async def import_transactions(
    db: AsyncSession, file_content: bytes, user_id
) -> dict:
    """Import transactions from Excel. Returns success/error summary."""
    from sqlalchemy import select

    wb = load_workbook(io.BytesIO(file_content), data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(min_row=2, values_only=True))
    results = {"success": [], "errors": []}

    for i, row in enumerate(rows, start=2):
        if len(row) < 5:
            results["errors"].append({"row": i, "error": "列数不足"})
            continue

        symbol = str(row[0]).strip() if row[0] else None
        tx_type = str(row[1]).strip() if row[1] else None

        errors = []
        if not symbol:
            errors.append("标的代码不能为空")
        if tx_type not in VALID_TX_TYPES:
            errors.append(f"交易类型无效: {tx_type}")

        quantity, err = _parse_decimal(row[2], "数量")
        if err:
            errors.append(err)
        price, err = _parse_decimal(row[3], "价格")
        if err:
            errors.append(err)
        tx_date, err = _parse_date(row[4])
        if err:
            errors.append(err)

        fee = Decimal("0")
        if len(row) > 5 and row[5]:
            fee, err = _parse_decimal(row[5], "手续费")
            if err:
                fee = Decimal("0")

        if errors:
            results["errors"].append({"row": i, "error": "; ".join(errors)})
            continue

        h_result = await db.execute(
            select(Holding).where(Holding.symbol == symbol)
        )
        holding = h_result.scalar_one_or_none()
        if not holding:
            results["errors"].append(
                {"row": i, "error": f"持仓不存在: {symbol}，请先添加持仓"}
            )
            continue

        transaction = Transaction(
            holding_id=holding.id,
            symbol=symbol,
            type=tx_type,
            quantity=quantity,
            price=price,
            fee=fee,
            date=tx_date,
            user_id=user_id,
        )
        db.add(transaction)
        results["success"].append({"row": i, "symbol": symbol, "type": tx_type})

    if results["success"]:
        await db.commit()

    return results
