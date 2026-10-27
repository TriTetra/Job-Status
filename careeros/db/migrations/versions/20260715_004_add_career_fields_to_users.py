"""Add career fields to users table

Revision ID: 004_users_career
Revises: 003_user_roles
Create Date: 2026-07-15
"""

from alembic import op
import sqlalchemy as sa


revision = '004_users_career'
down_revision = '003_user_roles'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('years_in_role', sa.Float, nullable=True))
    op.add_column('users', sa.Column('career_level', sa.String(20), nullable=True))
    op.add_column(
        'users',
        sa.Column('career_level_origin', sa.String(30), server_default='user')
    )
    op.add_column('users', sa.Column('current_role_id', sa.UUID, sa.ForeignKey('roles.id'), nullable=True))
    op.add_column('users', sa.Column('current_custom_role_id', sa.UUID, sa.ForeignKey('custom_roles.id'), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'current_custom_role_id')
    op.drop_column('users', 'current_role_id')
    op.drop_column('users', 'career_level_origin')
    op.drop_column('users', 'career_level')
    op.drop_column('users', 'years_in_role')
