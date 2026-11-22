"""applications: one row per (user, job) and a status history

The primary key was the job URL alone, so a second user tracking the same posting
hit a unique-key error. It becomes (user_id, url); the emails foreign key follows.
`history` keeps every status change ([{"status", "at"}]) for the application
drawer and Analytics; existing rows start from what they already record.

Revision ID: applications_017
Revises: invites_001
Create Date: 2026-11-23
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "applications_017"
down_revision = "invites_001"
branch_labels = None
depends_on = None


def _pk_name(bind, table: str) -> str:
    return sa.inspect(bind).get_pk_constraint(table)["name"]


def _fk_names(bind, table: str, referred: str) -> list[str]:
    return [fk["name"] for fk in sa.inspect(bind).get_foreign_keys(table) if fk["referred_table"] == referred]


def upgrade() -> None:
    bind = op.get_bind()
    for name in _fk_names(bind, "emails", "applications"):
        op.drop_constraint(name, "emails", type_="foreignkey")
    op.drop_constraint(_pk_name(bind, "applications"), "applications", type_="primary")
    op.create_primary_key("applications_pkey", "applications", ["user_id", "url"])
    op.create_foreign_key("emails_application_fkey", "emails", "applications",
                          ["user_id", "url"], ["user_id", "url"], ondelete="CASCADE")

    op.add_column("applications", sa.Column("history", postgresql.JSONB(), nullable=False,
                                            server_default=sa.text("'[]'::jsonb")))
    # Backfill: tracked when created, applied when applied_at says, now in its current status
    op.execute("""
        UPDATE applications SET history = (
            SELECT jsonb_agg(e ORDER BY e->>'at', CASE e->>'status' WHEN 'to_apply' THEN 0 WHEN 'applied' THEN 1 ELSE 2 END) FROM (
                SELECT jsonb_build_object('status', 'to_apply', 'at', to_char(LEAST(created_at, COALESCE(applied_at, created_at), updated_at) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"+00:00"')) AS e
                UNION ALL
                SELECT jsonb_build_object('status', 'applied', 'at', to_char(applied_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"+00:00"'))
                 WHERE applied_at IS NOT NULL AND status <> 'to_apply'
                UNION ALL
                SELECT jsonb_build_object('status', status, 'at', to_char(updated_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"+00:00"'))
                 WHERE status NOT IN ('to_apply', 'applied')
            ) events
        )
    """)


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_column("applications", "history")
    for name in _fk_names(bind, "emails", "applications"):
        op.drop_constraint(name, "emails", type_="foreignkey")
    op.drop_constraint(_pk_name(bind, "applications"), "applications", type_="primary")
    op.create_primary_key("applications_pkey", "applications", ["url"])
    op.create_foreign_key("emails_url_fkey", "emails", "applications", ["url"], ["url"], ondelete="CASCADE")
