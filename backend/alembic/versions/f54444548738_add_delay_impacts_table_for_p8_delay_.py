"""add delay_impacts table for P8 delay ripple

Revision ID: f54444548738
Revises: c81fbbc602b9
Create Date: 2026-09-06 02:53:21.947198

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f54444548738'
down_revision: Union[str, None] = 'c81fbbc602b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'delay_impacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('source_event_id', sa.Integer(), nullable=False),
        sa.Column('source_wbs_node_id', sa.Integer(), nullable=True),
        sa.Column('impacted_wbs_node_id', sa.Integer(), nullable=False),
        sa.Column('impact_type', sa.Enum('DIRECT', 'PROPAGATED', 'FLOAT_CONSUMED', 'CRITICAL_PATH', name='impacttype'), nullable=False),
        sa.Column('relationship_type', sa.String(), nullable=True),
        sa.Column('lag_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('original_delay_days', sa.Integer(), nullable=False),
        sa.Column('propagated_delay_days', sa.Integer(), nullable=False),
        sa.Column('float_consumed_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('remaining_float_days', sa.Integer(), nullable=True),
        sa.Column('is_critical_path', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('critical_path_exposure', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('path_depth', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['impacted_wbs_node_id'], ['wbs_nodes.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['source_event_id'], ['progress_events.id'], ),
        sa.ForeignKeyConstraint(['source_wbs_node_id'], ['wbs_nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_delay_impacts_id'), 'delay_impacts', ['id'], unique=False)
    op.create_index('ix_delay_impacts_project_event', 'delay_impacts', ['project_id', 'source_event_id'], unique=False)
    op.create_index('ix_delay_impacts_project_impacted', 'delay_impacts', ['project_id', 'impacted_wbs_node_id'], unique=False)
    op.create_index('ix_delay_impacts_critical', 'delay_impacts', ['project_id', 'is_critical_path'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_delay_impacts_critical', table_name='delay_impacts')
    op.drop_index('ix_delay_impacts_project_impacted', table_name='delay_impacts')
    op.drop_index('ix_delay_impacts_project_event', table_name='delay_impacts')
    op.drop_index(op.f('ix_delay_impacts_id'), table_name='delay_impacts')
    op.drop_table('delay_impacts')
    op.execute('DROP TYPE impacttype')