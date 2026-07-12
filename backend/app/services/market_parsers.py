"""行情原始报文解析：Decimal 转换、腾讯/东财字段解析。纯函数，无 I/O。"""

import math
import re
from decimal import Decimal


def _decimal_from_str(s: str | None) -> Decimal | None:
    if s is None:
        return None
    t = str(s).strip()
    if not t or t in ("-", "--"):
        return None
    try:
        return Decimal(t)
    except Exception:
        return None


def _parse_tencent_hk_us_line(inner: str) -> dict | None:
    """腾讯 r_hk / us 行情：~ 分隔，日期时间后接涨跌额、涨跌幅（与 A 股下标不同）。"""
    parts = inner.split("~")
    if len(parts) < 10:
        return None
    latest = _decimal_from_str(parts[3])
    if latest is None:
        return None
    prev = _decimal_from_str(parts[4])
    change: Decimal | None = None
    pct: Decimal | None = None
    for i, p in enumerate(parts):
        if p and re.search(r"\d{4}[-/]\d{2}[-/]\d{2}", p):
            if i + 2 < len(parts):
                change = _decimal_from_str(parts[i + 1])
                pct = _decimal_from_str(parts[i + 2])
            break
    if change is None and prev is not None:
        change = latest - prev
    if pct is None and prev is not None and prev > 0 and change is not None:
        pct = (change / prev) * Decimal(100)
    name = parts[1].strip() if len(parts) > 1 and parts[1] else None
    return {
        "latest_price": latest,
        "price_change": change if change is not None else Decimal("0"),
        "price_change_pct": pct if pct is not None else Decimal("0"),
        "name": name,
    }


def _parse_em_scaled_price(raw) -> Decimal | None:
    """东财 qt/stock/get 在 fltt=2 下，金额类字段多为实际值 ×100。"""
    if raw is None:
        return None
    if isinstance(raw, float) and math.isnan(raw):
        return None
    try:
        return Decimal(str(raw)) / Decimal(100)
    except Exception:
        return None
