"""add painting_logs table

Revision ID: 2ee719fdcf57
Revises: f356930f4fe9
Create Date: 2026-07-03 07:00:42.675892

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ee719fdcf57'
down_revision: Union[str, Sequence[str], None] = 'f356930f4fe9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'painting_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('log_time', sa.Text(), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_id', sa.Text(), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.Text(),
            server_default=sa.text("(datetime('now'))"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('painting_log')
