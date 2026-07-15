"""Create custom_roles table - user-defined roles with AI mapping

Revision ID: 002_custom_roles
Revises: 001_roles
Create Date: 2026-07-15
"""

from alembic import op
import sqlalchemy as sa


revision = '002_custom_roles'
down_revision = '001_roles'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'custom_roles',
        sa.Column('id', sa.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(128), sa.ForeignKey('users.clerk_id'), nullable=False),
        sa.Column('title', sa.String(150), nullable=False),
        sa.Column('mapped_role_id', sa.UUID, sa.ForeignKey('roles.id'), nullable=True),
        sa.Column('mapping_confidence', sa.Float, nullable=True),
        sa.Column('mapping_source', sa.String(30), nullable=True),
        sa.Column('mapping_metadata', sa.JSON, default=dict, server_default='{}'),
        sa.Column('mapped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index('idx_custom_roles_user', 'custom_roles', ['user_id'])
    op.create_index('idx_custom_roles_mapped', 'custom_roles', ['mapped_role_id'])


def downgrade() -> None:
    op.drop_index('idx_custom_roles_mapped', table_name='custom_roles')
    op.drop_index('idx_custom_roles_user', table_name='custom_roles')
    op.drop_table('custom_roles')
