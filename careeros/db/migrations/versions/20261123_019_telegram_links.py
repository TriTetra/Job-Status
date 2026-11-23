"""telegram_links: a user's Telegram chat for notifications

Revision ID: telegram_links_019
Revises: discovered_boards_018
Create Date: 2026-11-23
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "telegram_links_019"
down_revision = "discovered_boards_018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "telegram_links",
        sa.Column("user_id", sa.String(128), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("chat_id", sa.BigInteger(), nullable=True, unique=True),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("prefs", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{\"matches\": true, \"reminders\": true}'::jsonb")),
        sa.Column("sent", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("link_token_hash", sa.String(64), nullable=True),
        sa.Column("link_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_telegram_links_token", "telegram_links", ["link_token_hash"])


def downgrade() -> None:
    op.drop_index("idx_telegram_links_token", table_name="telegram_links")
    op.drop_table("telegram_links")
