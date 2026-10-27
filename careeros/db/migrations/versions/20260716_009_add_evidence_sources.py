"""Add evidence_sources table — metadata-driven connection registry

Revision ID: evidence_sources_001
Revises: sponsorship_001
"""
from alembic import op
import sqlalchemy as sa

revision = 'evidence_sources_001'
down_revision = 'sponsorship_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'evidence_sources',
        sa.Column('id', sa.String(50), primary_key=True),          # 'github', 'dribbble'
        sa.Column('label', sa.String(100), nullable=False),        # 'GitHub'
        sa.Column('icon', sa.String(50)),                          # frontend icon hint
        sa.Column('category', sa.String(50)),                      # code|design|data|academic|generic
        sa.Column('status', sa.String(20), nullable=False, server_default='coming_soon'),  # available|coming_soon
        sa.Column('oauth_provider', sa.String(50)),                # oauth router provider (github) veya null
        sa.Column('connect_kind', sa.String(20), server_default='oauth'),  # oauth|url|none
        sa.Column('sort_order', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default='now()'),
    )


def downgrade() -> None:
    op.drop_table('evidence_sources')
