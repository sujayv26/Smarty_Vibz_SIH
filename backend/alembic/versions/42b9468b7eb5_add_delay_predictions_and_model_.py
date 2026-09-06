"""add delay_predictions and model_training_runs tables for P10 ML delay prediction

Revision ID: 42b9468b7eb5
Revises: f54444548738
Create Date: 2026-09-06 10:46:25.094436

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42b9468b7eb5'
down_revision: Union[str, None] = 'f54444548738'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'delay_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('wbs_node_id', sa.Integer(), nullable=False),
        sa.Column('model_version', sa.String(), nullable=False, server_default='v1'),
        sa.Column('delay_probability', sa.Float(), nullable=False),
        sa.Column('expected_delay_days', sa.Float(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='risklevel'), nullable=False),
        sa.Column('feature_importance', sa.Text(), nullable=True),
        sa.Column('features_json', sa.Text(), nullable=True),
        sa.Column('prediction_date', sa.Date(), nullable=False),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['wbs_node_id'], ['wbs_nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_delay_predictions_id'), 'delay_predictions', ['id'], unique=False)
    op.create_index('ix_delay_predictions_project_node', 'delay_predictions', ['project_id', 'wbs_node_id'], unique=True)
    op.create_index('ix_delay_predictions_project_risk', 'delay_predictions', ['project_id', 'risk_level'], unique=False)
    op.create_index('ix_delay_predictions_date', 'delay_predictions', ['prediction_date'], unique=False)

    op.create_table(
        'model_training_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_version', sa.String(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('train_samples', sa.Integer(), nullable=False),
        sa.Column('test_samples', sa.Integer(), nullable=False),
        sa.Column('auc_roc', sa.Float(), nullable=True),
        sa.Column('auc_pr', sa.Float(), nullable=True),
        sa.Column('mae_delay_days', sa.Float(), nullable=True),
        sa.Column('rmse_delay_days', sa.Float(), nullable=True),
        sa.Column('feature_importance', sa.Text(), nullable=True),
        sa.Column('hyperparameters', sa.Text(), nullable=True),
        sa.Column('feature_list', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='completed'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_training_runs_id'), 'model_training_runs', ['id'], unique=False)
    op.create_index('ix_training_runs_project_version', 'model_training_runs', ['project_id', 'model_version'], unique=False)
    op.create_index('ix_training_runs_date', 'model_training_runs', ['started_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_training_runs_date', table_name='model_training_runs')
    op.drop_index('ix_training_runs_project_version', table_name='model_training_runs')
    op.drop_index(op.f('ix_model_training_runs_id'), table_name='model_training_runs')
    op.drop_table('model_training_runs')
    op.drop_index('ix_delay_predictions_date', table_name='delay_predictions')
    op.drop_index('ix_delay_predictions_project_risk', table_name='delay_predictions')
    op.drop_index('ix_delay_predictions_project_node', table_name='delay_predictions')
    op.drop_index(op.f('ix_delay_predictions_id'), table_name='delay_predictions')
    op.drop_table('delay_predictions')
    op.execute('DROP TYPE risklevel')