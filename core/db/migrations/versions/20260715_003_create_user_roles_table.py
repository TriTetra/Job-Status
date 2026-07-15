"""Create user_roles table - career history with XOR constraint

Revision ID: 003_user_roles
Revises: 002_custom_roles
Create Date: 2026-07-15
"""

from alembic import op
import sqlalchemy as sa


revision = '003_user_roles'
down_revision = '002_custom_roles'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_roles',
        sa.Column('id', sa.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(128), sa.ForeignKey('users.clerk_id'), nullable=False),
        sa.Column('role_id', sa.UUID, sa.ForeignKey('roles.id'), nullable=True),
        sa.Column('custom_role_id', sa.UUID, sa.ForeignKey('custom_roles.id'), nullable=True),
        sa.Column('started_at', sa.Date, nullable=False),
        sa.Column('ended_at', sa.Date, nullable=True),
        sa.Column('is_current', sa.Boolean, default=False, server_default='false'),
        sa.Column('source', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # XOR constraint: either role_id OR custom_role_id, never both
    op.create_check_constraint(
        'chk_role_xor_custom',
        'user_roles',
        '''
        (role_id IS NOT NULL AND custom_role_id IS NULL) OR
        (role_id IS NULL AND custom_role_id IS NOT NULL)
        '''
    )

    # Indexes
    op.create_index('idx_user_roles_user', 'user_roles', ['user_id'])
    op.create_index('idx_user_roles_role', 'user_roles', ['role_id'])
    op.create_index('idx_user_roles_custom', 'user_roles', ['custom_role_id'])
    
    # Partial index for current roles
    op.create_index(
        'idx_user_roles_current',
        'user_roles',
        ['user_id', 'is_current'],
        postgresql_where=sa.text('is_current = true')
    )

    # Unique constraint: only one current role per user
    op.create_index(
        'idx_user_roles_single_current',
        'user_roles',
        ['user_id'],
        unique=True,
        postgresql_where=sa.text('is_current = true')
    )


def downgrade() -> None:
    op.drop_index('idx_user_roles_single_current', table_name='user_roles')
    op.drop_index('idx_user_roles_current', table_name='user_roles')
    op.drop_index('idx_user_roles_custom', table_name='user_roles')
    op.drop_index('idx_user_roles_role', table_name='user_roles')
    op.drop_index('idx_user_roles_user', table_name='user_roles')
    op.drop_constraint('chk_role_xor_custom', 'user_roles', type_='check')
    op.drop_table('user_roles')
