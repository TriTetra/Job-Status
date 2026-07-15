"""Add career_preferences table

Revision ID: career_prefs_001
Revises: 005_role_aliases
Create Date: 2026-07-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision = 'career_prefs_001'
down_revision = '005_role_aliases'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'career_preferences',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(128), sa.ForeignKey('users.clerk_id'), nullable=False),

        sa.Column('goal_ids', JSONB, server_default='[]'),
        sa.Column('preferred_role_ids', JSONB, server_default='[]'),
        sa.Column('preferred_country_codes', JSONB, server_default='[]'),
        sa.Column('work_arrangements', JSONB, server_default='[]'),

        sa.Column('salary_min', sa.Integer, nullable=True),
        sa.Column('salary_max', sa.Integer, nullable=True),
        sa.Column('salary_currency', sa.String(3), nullable=True),
        sa.Column('salary_period', sa.String(10), server_default='year'),
        sa.Column('salary_negotiable', sa.Boolean, server_default='true'),

        sa.Column('pref_metadata', JSONB, server_default='{}'),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('idx_career_preferences_user', 'career_preferences', ['user_id'], unique=True)
    op.create_index('idx_career_preferences_goals', 'career_preferences', ['goal_ids'], postgresql_using='gin')
    op.create_index('idx_career_preferences_roles', 'career_preferences', ['preferred_role_ids'], postgresql_using='gin')
    op.create_index('idx_career_preferences_countries', 'career_preferences', ['preferred_country_codes'], postgresql_using='gin')


def downgrade() -> None:
    op.drop_index('idx_career_preferences_countries', table_name='career_preferences')
    op.drop_index('idx_career_preferences_roles', table_name='career_preferences')
    op.drop_index('idx_career_preferences_goals', table_name='career_preferences')
    op.drop_index('idx_career_preferences_user', table_name='career_preferences')
    op.drop_table('career_preferences')
