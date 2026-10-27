"""Create roles table - canonical tech roles with metadata

Revision ID: 001_roles
Revises: e1f2a3b4c5d6
Create Date: 2026-07-15

This is the foundation of Aplio's Career Intelligence Graph.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = '001_roles'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('slug', sa.String(50), nullable=False, unique=True),
        sa.Column('title', sa.String(150), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('aliases', JSONB, default=list, server_default='[]'),
        sa.Column('metadata', JSONB, default=dict, server_default='{}'),
        sa.Column('version', sa.Integer, default=1, server_default='1'),
        sa.Column('esco_id', sa.String(50), nullable=True),
        sa.Column('soc_code', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index('idx_roles_slug', 'roles', ['slug'])
    op.create_index('idx_roles_category', 'roles', ['category'])
    op.create_index('idx_roles_title', 'roles', ['title'])
    op.create_index('idx_roles_metadata', 'roles', ['metadata'], postgresql_using='gin')


def downgrade() -> None:
    op.drop_index('idx_roles_metadata', table_name='roles')
    op.drop_index('idx_roles_title', table_name='roles')
    op.drop_index('idx_roles_category', table_name='roles')
    op.drop_index('idx_roles_slug', table_name='roles')
    op.drop_table('roles')
