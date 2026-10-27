"""add_jobs_table

Revision ID: a1b2c3d4e5f6
Revises: 0f3bcfe43a4e
Create Date: 2026-07-14 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a1b2c3d4e5f6'
down_revision = '0f3bcfe43a4e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'jobs',
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False, server_default=''),
        sa.Column('company', sa.String(length=256), nullable=False, server_default=''),
        sa.Column('location', sa.String(length=256), nullable=False, server_default=''),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('full_description', sa.Text(), nullable=True),
        sa.Column('site', sa.String(length=64), nullable=True),
        sa.Column('source', sa.String(length=64), nullable=False, server_default='applypilot'),
        sa.Column('application_url', sa.String(length=2048), nullable=True),
        sa.Column('fit_score', sa.Float(), nullable=True),
        sa.Column('score_reasoning', sa.Text(), nullable=True),
        sa.Column('salary_min', sa.Integer(), nullable=True),
        sa.Column('salary_max', sa.Integer(), nullable=True),
        sa.Column('required_years', sa.Float(), nullable=True),
        sa.Column('company_size', sa.String(length=32), nullable=True),
        sa.Column('remote', sa.Boolean(), nullable=True),
        sa.Column('required_skills', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('discovered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('url'),
    )
    op.create_index('idx_jobs_company', 'jobs', ['company'], unique=False)
    op.create_index('idx_jobs_site', 'jobs', ['site'], unique=False)
    op.create_index('idx_jobs_source', 'jobs', ['source'], unique=False)
    op.create_index('idx_jobs_fit_score', 'jobs', ['fit_score'], unique=False)
    op.create_index('idx_jobs_discovered_at', 'jobs', ['discovered_at'], unique=False)
    op.create_index('idx_jobs_skills_gin', 'jobs', ['required_skills'], unique=False, postgresql_using='gin')


def downgrade() -> None:
    op.drop_index('idx_jobs_skills_gin', table_name='jobs')
    op.drop_index('idx_jobs_discovered_at', table_name='jobs')
    op.drop_index('idx_jobs_fit_score', table_name='jobs')
    op.drop_index('idx_jobs_source', table_name='jobs')
    op.drop_index('idx_jobs_site', table_name='jobs')
    op.drop_index('idx_jobs_company', table_name='jobs')
    op.drop_table('jobs')
