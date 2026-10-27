"""llm gateway: llm_calls usage log, LLM-extracted facts on jobs

Revision ID: llm_gateway_001
Revises: job_boards_001
Create Date: 2026-10-28
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "llm_gateway_001"
down_revision = "job_boards_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_calls",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("task", sa.String(32), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("user_id", sa.String(128), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cost_estimated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_index("idx_llm_calls_created", "llm_calls", ["created_at"])
    op.create_index("idx_llm_calls_user_created", "llm_calls", ["user_id", "created_at"])

    op.add_column("jobs", sa.Column("llm_facts", postgresql.JSONB(), nullable=True))
    op.add_column("jobs", sa.Column("llm_facts_hash", sa.String(64), nullable=True))
    op.add_column("jobs", sa.Column("llm_model", sa.String(128), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "llm_model")
    op.drop_column("jobs", "llm_facts_hash")
    op.drop_column("jobs", "llm_facts")
    op.drop_index("idx_llm_calls_user_created", table_name="llm_calls")
    op.drop_index("idx_llm_calls_created", table_name="llm_calls")
    op.drop_table("llm_calls")
