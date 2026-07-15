"""Create role_aliases table - title evolution tracking

Revision ID: 005_role_aliases
Revises: 004_users_career
Create Date: 2026-07-15
"""

from alembic import op
import sqlalchemy as sa


revision = '005_role_aliases'
down_revision = '004_users_career'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'role_aliases',
        sa.Column('id', sa.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('role_id', sa.UUID, sa.ForeignKey('roles.id'), nullable=False),
        sa.Column('old_title', sa.String(150), nullable=False),
        sa.Column('new_title', sa.String(150), nullable=False),
        sa.Column('old_slug', sa.String(50), nullable=True),
        sa.Column('new_slug', sa.String(50), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('changed_by', sa.String(50), nullable=True),
        sa.Column('reason', sa.String(255), nullable=True),
    )

    # Indexes
    op.create_index('idx_role_aliases_role', 'role_aliases', ['role_id'])
    op.create_index('idx_role_aliases_old_title', 'role_aliases', ['old_title'])
    op.create_index('idx_role_aliases_old_slug', 'role_aliases', ['old_slug'])


def downgrade() -> None:
    op.drop_index('idx_role_aliases_old_slug', table_name='role_aliases')
    op.drop_index('idx_role_aliases_old_title', table_name='role_aliases')
    op.drop_index('idx_role_aliases_role', table_name='role_aliases')
    op.drop_table('role_aliases')
