"""add sector, purchase_date, cost_method to holdings; add daily_return to snapshots

Revision ID: a1b2c3d4e5f6
Revises: 9ac5273b1103
Create Date: 2026-05-20 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9ac5273b1103'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Holdings: add sector, purchase_date, cost_method ---
    op.add_column('holdings', sa.Column('sector', sa.String(50), nullable=True, comment='申万一级行业分类'))
    op.add_column('holdings', sa.Column('purchase_date', sa.DateTime(), nullable=True, comment='首次买入日期'))
    # Create enum type for cost_method
    cost_method_enum = sa.Enum('fifo', 'average', name='cost_method_enum')
    cost_method_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('holdings', sa.Column(
        'cost_method', cost_method_enum, nullable=False, server_default='fifo',
        comment='成本计算方法: fifo=先进先出, average=平均成本',
    ))

    # --- Snapshots: add daily_return ---
    op.add_column('snapshots', sa.Column('daily_return', sa.Float(), nullable=True, comment='日收益率(%)'))


def downgrade() -> None:
    # --- Snapshots ---
    op.drop_column('snapshots', 'daily_return')

    # --- Holdings ---
    op.drop_column('holdings', 'cost_method')
    # Drop enum type
    cost_method_enum = sa.Enum('fifo', 'average', name='cost_method_enum')
    cost_method_enum.drop(op.get_bind(), checkfirst=True)
    op.drop_column('holdings', 'purchase_date')
    op.drop_column('holdings', 'sector')
