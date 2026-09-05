"""add actual_start actual_finish to schedule_activities

Revision ID: c81fbbc602b9
Revises: d688256165ff
Create Date: 2026-09-05 22:11:28.307542

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c81fbbc602b9'
down_revision: Union[str, None] = 'd688256165ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('schedule_activities', sa.Column('actual_start', sa.Date(), nullable=True))
    op.add_column('schedule_activities', sa.Column('actual_finish', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('schedule_activities', 'actual_finish')
    op.drop_column('schedule_activities', 'actual_start')
