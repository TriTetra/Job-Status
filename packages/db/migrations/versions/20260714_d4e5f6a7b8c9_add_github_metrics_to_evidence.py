"""add_github_metrics_to_evidence

Adds real GitHub metrics columns to the evidence table.
Populated by plugins/enrichment/github/evidence_enricher.py.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-14 17:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("evidence", sa.Column("loc_count", sa.Integer(), nullable=True))
    op.add_column("evidence", sa.Column("language", sa.String(100), nullable=True))
    op.add_column("evidence", sa.Column("topics", JSONB(), nullable=True))
    op.add_column("evidence", sa.Column("pr_count", sa.Integer(), nullable=True))
    op.add_column("evidence", sa.Column("issue_count", sa.Integer(), nullable=True))
    op.add_column("evidence", sa.Column("has_releases", sa.Boolean(), nullable=True))
    op.add_column("evidence", sa.Column("has_tests", sa.Boolean(), nullable=True))
    op.add_column("evidence", sa.Column("has_docs", sa.Boolean(), nullable=True))
    op.add_column(
        "evidence",
        sa.Column("last_commit_date", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    for col in [
        "last_commit_date", "has_docs", "has_tests", "has_releases",
        "issue_count", "pr_count", "topics", "language", "loc_count",
    ]:
        op.drop_column("evidence", col)
