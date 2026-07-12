"""convert datetime columns to timezone-aware (timestamptz)

Revision ID: c7d8e9f01234
Revises: a1b2c3d4e5f6
Create Date: 2026-07-12 10:20:00.000000

已有的 naive 时间戳按 UTC 解释后转换为 timestamptz。
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f01234'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (table, column) 需要从 timestamp 转为 timestamptz 的列
_DATETIME_COLUMNS: tuple[tuple[str, str], ...] = (
    ("users", "created_at"),
    ("holdings", "latest_price_updated_at"),
    ("holdings", "purchase_date"),
    ("holdings", "created_at"),
    ("holdings", "updated_at"),
    ("transactions", "created_at"),
    ("allocation_targets", "updated_at"),
    ("price_cache", "updated_at"),
    ("ai_conversations", "created_at"),
    ("daily_reports", "created_at"),
    ("memos", "created_at"),
    ("memos", "updated_at"),
    ("operation_logs", "created_at"),
    ("snapshots", "created_at"),
)


def upgrade() -> None:
    for table, column in _DATETIME_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    for table, column in _DATETIME_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(),
            existing_type=sa.DateTime(timezone=True),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
