"""apply_kits: a prepared application per user and job (form questions, suggested answers, CV, note)

Revision ID: apply_kits_022
Revises: person_memory_021
Create Date: 2026-11-23
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "apply_kits_022"
down_revision = "person_memory_021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "apply_kits",
        sa.Column("user_id", sa.String(128), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("url", sa.String(2048), primary_key=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("apply_kits")
