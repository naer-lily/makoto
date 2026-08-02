"""add fiber_per_100g to food

Revision ID: a1b2c3d4e5f6
Revises: 2ee719fdcf57
Create Date: 2026-08-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '2ee719fdcf57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('food') as batch_op:
        batch_op.add_column(
            sa.Column(
                'fiber_per_100g',
                sa.Float(),
                nullable=False,
                server_default=sa.text('0.0'),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table('food') as batch_op:
        batch_op.drop_column('fiber_per_100g')
