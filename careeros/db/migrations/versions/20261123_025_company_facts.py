"""company_facts: public facts about employers (Wikidata, Companies House, Hacker News), with sources

Revision ID: company_facts_025
Revises: mail_signals_024
Create Date: 2026-11-23
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "company_facts_025"
down_revision = "mail_signals_024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_facts",
        sa.Column("key", sa.String(200), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("wikidata", postgresql.JSONB(), nullable=True),
        sa.Column("companies_house", postgresql.JSONB(), nullable=True),
        sa.Column("people", postgresql.JSONB(), nullable=True),
        sa.Column("read_at", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("company_facts")
