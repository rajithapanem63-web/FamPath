"""Add preference_responses table

Revision ID: 876b4322dd6d
Revises: 
Create Date: 2026-10-18 09:49:29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Use GUID for SQLite compat
try:
    from app.models.base import GUID
except:
    GUID = sa.String(36)


def upgrade():
    op.create_table(
        'preference_responses',
        sa.Column('id', GUID, nullable=False),
        sa.Column('workspace_id', GUID, nullable=False),
        sa.Column('user_id', GUID, nullable=False),
        sa.Column('dimension', sa.String(50), nullable=False),
        sa.Column('weight', sa.Integer(), nullable=False),
        sa.Column('selected_options', sa.JSON(), nullable=False),
        sa.Column('additional_data', sa.JSON(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('weight IN (3, 6, 9)', name='valid_weight'),
        sa.CheckConstraint(
            \"dimension IN ('branch_preference', 'location_preference', 'college_type_preference', 'budget_constraint', 'placement_importance', 'campus_facilities', 'reputation_ranking', 'career_goal')\",
            name='valid_dimension'
        ),
        sa.ForeignKeyConstraint(['workspace_id'], ['family_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'user_id', 'dimension', 'version', name='unique_preference_version')
    )
    
    op.create_index('idx_pref_workspace_user', 'preference_responses', ['workspace_id', 'user_id'])
    op.create_index('idx_pref_active', 'preference_responses', ['is_active'])
    op.create_index('idx_pref_dimension', 'preference_responses', ['dimension'])


def downgrade():
    op.drop_index('idx_pref_dimension', table_name='preference_responses')
    op.drop_index('idx_pref_active', table_name='preference_responses')
    op.drop_index('idx_pref_workspace_user', table_name='preference_responses')
    op.drop_table('preference_responses')
