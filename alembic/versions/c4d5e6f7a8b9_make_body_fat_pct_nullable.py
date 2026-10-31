"""make body_fat_pct nullable for BIA cleanup

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-10-31 13:15:00.000000

BIA 体成分读数按主人要求全部清空，body_log / profile 的 body_fat_pct
不再有值，因此列约束改为可空。实际数据清空由一次性受控迁移完成；
本迁移只保证 schema 与代码模型一致。
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: str | Sequence[str] | None = 'b2c3d4e5f6a7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('body_log') as batch_op:
        batch_op.alter_column(
            'body_fat_pct', existing_type=sa.Float(), nullable=True
        )
    with op.batch_alter_table('profile') as batch_op:
        batch_op.alter_column(
            'body_fat_pct', existing_type=sa.Float(), nullable=True
        )


def downgrade() -> None:
    # 若仍有 NULL 值，SQLite 重建表时会失败；这是有意的安全阀。
    with op.batch_alter_table('profile') as batch_op:
        batch_op.alter_column(
            'body_fat_pct', existing_type=sa.Float(), nullable=False
        )
    with op.batch_alter_table('body_log') as batch_op:
        batch_op.alter_column(
            'body_fat_pct', existing_type=sa.Float(), nullable=False
        )
