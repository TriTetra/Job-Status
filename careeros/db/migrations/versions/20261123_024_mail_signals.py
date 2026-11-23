"""mail_signals: employer answers found in a person's mailbox (facts only, never bodies)

Revision ID: mail_signals_024
Revises: jobs_added_by_023
Create Date: 2026-11-23
"""

import sqlalchemy as sa
from alembic import op

revision = "mail_signals_024"
down_revision = "jobs_added_by_023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mail_signals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(128), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_key", sa.String(64), nullable=False),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("company", sa.String(200), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("from_domain", sa.String(200), nullable=False, server_default=""),
        sa.Column("subject", sa.String(300), nullable=False, server_default=""),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("evidence", sa.String(300), nullable=False, server_default=""),
        sa.Column("state", sa.String(12), nullable=False),
        sa.Column("status_before", sa.String(20), nullable=True),
        sa.Column("status_after", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "message_key", name="uq_mail_signals_user_message"),
    )
    op.create_index("idx_mail_signals_user_state", "mail_signals", ["user_id", "state"])


def downgrade() -> None:
    op.drop_index("idx_mail_signals_user_state", table_name="mail_signals")
    op.drop_table("mail_signals")
