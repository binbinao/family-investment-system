"""时间工具：统一提供 timezone-aware 的 UTC 当前时间。

替代已弃用的 ``datetime.utcnow()``（返回 naive），确保与
``DateTime(timezone=True)`` 列一致，避免 naive/aware 混用报错。
"""

from datetime import UTC, datetime


def utcnow() -> datetime:
    """返回 timezone-aware 的 UTC 当前时间。"""
    return datetime.now(UTC)
