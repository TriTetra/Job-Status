"""own auth: users.clerk_id -> users.id, password credentials, server-side sessions

Clerk is removed. Existing user ids (Clerk's "user_…" strings) are kept as-is,
so every row that references a user keeps working; foreign keys follow the
column rename automatically.

Revision ID: own_auth_001
Revises: market_skills_001
Create Date: 2026-10-28 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "own_auth_001"
down_revision = "market_skills_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "clerk_id", new_column_name="id")
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))

    op.create_table(
        "auth_credentials",
        sa.Column("user_id", sa.String(128), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "auth_sessions",
        # sha256 of the cookie token — the token itself is never stored
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(128), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent", sa.String(300), nullable=True),
        sa.Column("ip", sa.String(64), nullable=True),
    )
    op.create_index("idx_auth_sessions_user", "auth_sessions", ["user_id"])
    op.create_index("idx_auth_sessions_expires", "auth_sessions", ["expires_at"])


def downgrade() -> None:
    op.drop_index("idx_auth_sessions_expires", table_name="auth_sessions")
    op.drop_index("idx_auth_sessions_user", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_table("auth_credentials")
    op.drop_column("users", "is_active")
    op.alter_column("users", "id", new_column_name="clerk_id")
