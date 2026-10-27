"""Goals registry — role-aware, no hardcoded goal list.

Revision ID: goals_registry_001
Revises: matching_fields_001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'goals_registry_001'
down_revision = 'matching_fields_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'goals',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('label', sa.String(100), nullable=False),
        sa.Column('theme', sa.String(30), nullable=False),
        sa.Column('applicable', JSONB, nullable=False),
        sa.Column('priority_for', JSONB, nullable=False, server_default='[]'),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0'),
    )


def downgrade() -> None:
    op.drop_table('goals')
