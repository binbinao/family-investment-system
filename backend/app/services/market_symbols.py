"""标的代码解析与规范化：市场判定、A股/港股/美股代码转换。纯函数，无 I/O。"""

import re


def _equity_market(symbol: str) -> str:
    """标的所属市场：cn A 股、hk 港股、us 美股（用于选用行情接口）。"""
    raw = str(symbol).strip()
    u = raw.upper()
    if u.endswith(".HK"):
        return "hk"
    for suf in (".US", ".NYSE", ".NASDAQ", ".OQ"):
        if u.endswith(suf):
            return "us"
    if u.endswith(".N") and len(u) > 4:
        return "us"
    for suf in (".SH", ".SZ", ".BJ", ".SS"):
        if u.endswith(suf):
            return "cn"
    letters = re.sub(r"[^A-Za-z]", "", raw)
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits and not letters:
        if len(digits) == 6:
            return "cn"
        if len(digits) == 5:
            return "hk"
    if letters:
        return "us"
    return "cn"


def _hk_code_5(symbol: str) -> str:
    """港股 5 位代码，如 00700、00001。"""
    raw = str(symbol).strip().upper()
    base = raw[: -3] if raw.endswith(".HK") else raw
    d = "".join(ch for ch in base if ch.isdigit())
    if not d:
        return ""
    if len(d) > 5:
        d = d[-5:]
    return d.zfill(5)


def _us_ticker_pair(symbol: str) -> tuple[str, str]:
    """(腾讯 q 参数前缀+代码, 新浪 gb_ 后缀)。腾讯示例 usAAPL、usBRK.B；新浪 gb_aapl、gb_brkb。"""
    raw = str(symbol).strip().upper()
    for suf in (".US", ".NYSE", ".NASDAQ", ".OQ"):
        if raw.endswith(suf):
            raw = raw[: -len(suf)]
            break
    if raw.endswith(".N") and len(raw) > 4:
        raw = raw[:-2]
    tick = raw.replace("-", ".")
    if not tick or not re.search(r"[A-Z]", tick):
        return "", ""
    tencent = "us" + tick
    sina_suffix = tick.lower().replace(".", "")
    return tencent, sina_suffix


def _normalize_stock_symbol(symbol: str) -> str:
    """将用户输入规范为 A 股 6 位代码，便于与东财 spot 表「代码」列匹配。"""
    if _equity_market(symbol) != "cn":
        return str(symbol).strip()
    raw = str(symbol).strip().upper()
    for suf in (".SH", ".SZ", ".BJ", ".SS"):
        if raw.endswith(suf):
            raw = raw[: -len(suf)]
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return str(symbol).strip()
    if len(digits) <= 6:
        return digits.zfill(6)
    return digits[-6:]


def _spot_em_code_key(col):
    """统一行情表代码列为 6 位字符串（兼容 int/float/str）。"""
    s = col.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()

    def to_key(x: str) -> str:
        x = str(x).strip()
        if x.isdigit():
            return x.zfill(6)
        return x

    return s.map(to_key)


def _vendor_list_code(norm: str) -> str:
    """新浪/腾讯 list 参数：沪 sh、深 sz、北交所 920 段为 bj。"""
    if norm.startswith("920"):
        return f"bj{norm}"
    if norm.startswith("6"):
        return f"sh{norm}"
    return f"sz{norm}"


def _eastmoney_market_prefix(norm: str) -> int:
    """东财 secid 市场前缀：沪市 1，其余（深/北交所 920 等）0。与 AKShare 单票接口一致。"""
    return 1 if norm.startswith("6") else 0
