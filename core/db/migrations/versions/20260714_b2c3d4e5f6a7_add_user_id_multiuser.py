"""add_user_id_multiuser

Adds user_id to all user-data tables for multi-user data isolation.
Existing rows are backfilled to user_id='default'.
Primary keys are left unchanged to preserve the emails FK.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-14 13:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # career_scores
    op.add_column('career_scores', sa.Column('user_id', sa.String(100), nullable=False, server_default='default'))
    op.create_index('idx_career_scores_user', 'career_scores', ['user_id'])

    # applications
    op.add_column('applications', sa.Column('user_id', sa.String(100), nullable=False, server_default='default'))
    op.create_index('idx_applications_user', 'applications', ['user_id'])

    # emails
    op.add_column('emails', sa.Column('user_id', sa.String(100), nullable=False, server_default='default'))
    op.create_index('idx_emails_user', 'emails', ['user_id'])

    # scan_history
    op.add_column('scan_history', sa.Column('user_id', sa.String(100), nullable=False, server_default='default'))
    op.create_index('idx_scan_history_user', 'scan_history', ['user_id'])

    # evidence
    op.add_column('evidence', sa.Column('user_id', sa.String(100), nullable=False, server_default='default'))
    op.create_index('idx_evidence_user', 'evidence', ['user_id'])

    # jobs (shared across users — no user_id needed; it's a canonical catalog)


def downgrade() -> None:
    op.drop_index('idx_evidence_user', table_name='evidence')
    op.drop_column('evidence', 'user_id')

    op.drop_index('idx_scan_history_user', table_name='scan_history')
    op.drop_column('scan_history', 'user_id')

    op.drop_index('idx_emails_user', table_name='emails')
    op.drop_column('emails', 'user_id')

    op.drop_index('idx_applications_user', table_name='applications')
    op.drop_column('applications', 'user_id')

    op.drop_index('idx_career_scores_user', table_name='career_scores')
    op.drop_column('career_scores', 'user_id')
