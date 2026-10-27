"""company job boards: jobs lifecycle columns, job_board_runs, one score per (user, job)

career_scores was append-only (a new row per job per scan). It now keeps the
latest row per (user_id, url) — older rows are deleted, the earliest scan time
is kept in first_scored_at.

Revision ID: job_boards_001
Revises: own_auth_001
Create Date: 2026-10-28
"""

import sqlalchemy as sa
from alembic import op

revision = "job_boards_001"
down_revision = "own_auth_001"
branch_labels = None
depends_on = None

TZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    # ── jobs: where a posting came from and whether it is still open ──
    for name, col in [
        ("department", sa.String(256)),
        ("employment_type", sa.String(64)),
        ("company_key", sa.String(64)),
        ("ats", sa.String(32)),
        ("external_id", sa.String(128)),
        ("salary_currency", sa.String(8)),
        ("remote_region", sa.String(64)),
        ("sponsors_visa", sa.Boolean()),
        ("content_hash", sa.String(64)),
        ("posted_at", TZ),
        ("last_seen_at", TZ),
        ("closed_at", TZ),
    ]:
        op.add_column("jobs", sa.Column(name, col, nullable=True))
    op.create_index("idx_jobs_company_key", "jobs", ["company_key"])
    op.create_index("idx_jobs_open", "jobs", ["discovered_at"], postgresql_where=sa.text("closed_at IS NULL"))

    op.create_table(
        "job_board_runs",
        sa.Column("company_key", sa.String(64), primary_key=True),
        sa.Column("last_run_at", TZ, nullable=False),
        sa.Column("last_success_at", TZ, nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("kept", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("closed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
    )

    # ── career_scores: keep the latest row per (user, job) ──
    op.add_column("career_scores", sa.Column("first_scored_at", sa.DateTime(), nullable=True))
    op.add_column("career_scores", sa.Column("input_hash", sa.String(64), nullable=True))
    op.execute("""
        UPDATE career_scores cs SET first_scored_at = f.first
        FROM (SELECT user_id, url, MIN(scanned_at) AS first FROM career_scores GROUP BY user_id, url) f
        WHERE cs.user_id = f.user_id AND cs.url = f.url
    """)
    op.execute("""
        DELETE FROM career_scores a USING career_scores b
        WHERE a.user_id = b.user_id AND a.url = b.url AND a.scanned_at < b.scanned_at
    """)
    op.drop_constraint("career_scores_pkey", "career_scores", type_="primary")
    op.create_primary_key("career_scores_pkey", "career_scores", ["user_id", "url"])
    op.alter_column("career_scores", "user_id", server_default=None)


def downgrade() -> None:
    op.alter_column("career_scores", "user_id", server_default="default")
    op.drop_constraint("career_scores_pkey", "career_scores", type_="primary")
    op.create_primary_key("career_scores_pkey", "career_scores", ["url", "scanned_at"])
    op.drop_column("career_scores", "input_hash")
    op.drop_column("career_scores", "first_scored_at")

    op.drop_table("job_board_runs")
    op.drop_index("idx_jobs_open", table_name="jobs")
    op.drop_index("idx_jobs_company_key", table_name="jobs")
    for name in ("closed_at", "last_seen_at", "posted_at", "content_hash", "sponsors_visa", "remote_region",
                 "salary_currency", "external_id", "ats", "company_key", "employment_type", "department"):
        op.drop_column("jobs", name)
