"""web accounts: users.is_admin, auth_invites (single-use sign-up links)

The oldest existing user (if any) becomes admin, so a database that already has
accounts keeps someone who can invite.

Revision ID: invites_001
Revises: llm_gateway_001
Create Date: 2026-11-22
"""

import sqlalchemy as sa
from alembic import op

revision = "invites_001"
down_revision = "llm_gateway_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute("UPDATE users SET is_admin = true WHERE id = (SELECT id FROM users ORDER BY created_at LIMIT 1)")
    op.create_table(
        "auth_invites",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("created_by", sa.String(128), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("used_by", sa.String(128), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("auth_invites")
    op.drop_column("users", "is_admin")
