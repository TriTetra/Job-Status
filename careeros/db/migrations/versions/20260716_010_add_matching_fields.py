"""Add contract_types, availability, target_seniority to career_preferences.

Revision ID: matching_fields_001
Revises: evidence_sources_001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'matching_fields_001'
down_revision = 'evidence_sources_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('career_preferences', sa.Column('contract_types', JSONB, server_default='[]'))
    op.add_column('career_preferences', sa.Column('availability', sa.String(30), nullable=True))
    op.add_column('career_preferences', sa.Column('target_seniority', sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column('career_preferences', 'target_seniority')
    op.drop_column('career_preferences', 'availability')
    op.drop_column('career_preferences', 'contract_types')
