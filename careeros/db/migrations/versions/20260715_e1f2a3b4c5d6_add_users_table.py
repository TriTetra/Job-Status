"""add_users_table

Revision ID: e1f2a3b4c5d6
Revises: 0a137256f663
Create Date: 2026-07-15 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'e1f2a3b4c5d6'
down_revision = '0a137256f663'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('clerk_id', sa.String(length=128), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('image_url', sa.String(length=1024), nullable=True),
        sa.Column('onboarding_state', sa.String(length=32), nullable=False, server_default='NOT_STARTED'),
        sa.Column('profile_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('goals', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('clerk_id'),
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
