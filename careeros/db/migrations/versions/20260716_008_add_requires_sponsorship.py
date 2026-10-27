"""Add requires_sponsorship to career_preferences

Revision ID: sponsorship_001
Revises: evidence_intel_001
Create Date: 2026-07-16
"""
from alembic import op
import sqlalchemy as sa

revision = 'sponsorship_001'
down_revision = 'evidence_intel_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'career_preferences',
        sa.Column('requires_sponsorship', sa.Boolean(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('career_preferences', 'requires_sponsorship')
