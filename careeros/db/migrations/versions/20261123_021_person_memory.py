"""person_events and job_impressions: the person memory log and what was shown

person_events is append-only: one row per thing that happened with the person (a decision
and its reasons, an application stage, a CV upload, new evidence, a preference change),
with who said it (actor) and two clocks (valid_from, recorded_at). job_impressions keeps
which jobs were shown where and at which rank, once per day.

Revision ID: person_memory_021
Revises: job_company_domain_020
Create Date: 2026-11-23
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "person_memory_021"
down_revision = "job_company_domain_020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "person_events",
        sa.Column("seq", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(128), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stream", sa.String(160), nullable=False),
        sa.Column("stream_version", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("schema_ver", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("actor", sa.String(64), nullable=False, server_default="user"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source_ref", postgresql.JSONB(), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("causation_id", sa.BigInteger(), nullable=True),
        sa.Column("correlation_id", sa.String(64), nullable=True),
        sa.UniqueConstraint("user_id", "stream", "stream_version", name="uq_person_events_stream_version"),
    )
    op.create_index("idx_person_events_user_time", "person_events", ["user_id", "recorded_at"])
    op.create_index("idx_person_events_user_type", "person_events", ["user_id", "type"])
    op.create_table(
        "job_impressions",
        sa.Column("user_id", sa.String(128), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("url", sa.String(2048), primary_key=True),
        sa.Column("surface", sa.String(16), primary_key=True),
        sa.Column("day", sa.Date(), primary_key=True),
        sa.Column("best_rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("times", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_shown_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_shown_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("job_impressions")
    op.drop_index("idx_person_events_user_type", table_name="person_events")
    op.drop_index("idx_person_events_user_time", table_name="person_events")
    op.drop_table("person_events")
