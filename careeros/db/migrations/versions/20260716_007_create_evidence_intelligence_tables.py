"""create_evidence_intelligence_tables

Revision ID: evidence_intel_001
Revises: career_prefs_001
Create Date: 2026-07-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'evidence_intel_001'
down_revision = 'career_prefs_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'resume_documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('storage_key', sa.String(512), nullable=True),
        sa.Column('content_type', sa.String(100), nullable=False, server_default='application/pdf'),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('parse_status', sa.String(32), nullable=False, server_default='pending'),
        sa.Column('parsed_text', sa.Text(), nullable=True),
        sa.Column('parse_result', postgresql.JSONB(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_resume_documents_user_id', 'resume_documents', ['user_id'])

    op.create_table(
        'skills',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(150), nullable=False),
        sa.Column('slug', sa.String(150), nullable=False),
        sa.Column('category', sa.String(80), nullable=False),
        sa.Column('subcategory', sa.String(80), nullable=True),
        sa.Column('aliases', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('related_skill_ids', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('skill_metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_deprecated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('idx_skills_category', 'skills', ['category'])
    op.create_index('idx_skills_slug', 'skills', ['slug'])

    op.create_table(
        'evidence_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('skill_id', sa.Integer(), sa.ForeignKey('skills.id', ondelete='SET NULL'), nullable=True),
        sa.Column('skill_name', sa.String(150), nullable=False),
        sa.Column('source', sa.String(32), nullable=False),
        sa.Column('source_url', sa.String(512), nullable=True),
        sa.Column('source_ref', sa.String(256), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('depth_score', sa.Float(), nullable=True),
        sa.Column('evidence_text', sa.Text(), nullable=True),
        sa.Column('evidence_data', postgresql.JSONB(), nullable=True),
        sa.Column('resume_document_id', sa.Integer(),
                  sa.ForeignKey('resume_documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_evidence_items_user_id', 'evidence_items', ['user_id'])
    op.create_index('idx_evidence_items_user_skill', 'evidence_items', ['user_id', 'skill_name'])
    op.create_index('idx_evidence_items_confidence', 'evidence_items', ['confidence_score'])

    op.create_table(
        'connected_accounts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('provider', sa.String(32), nullable=False),
        sa.Column('provider_user_id', sa.String(256), nullable=True),
        sa.Column('provider_username', sa.String(256), nullable=True),
        sa.Column('access_token', sa.String(2048), nullable=True),
        sa.Column('refresh_token', sa.String(2048), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scopes', postgresql.JSONB(), nullable=True),
        sa.Column('account_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_status', sa.String(32), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_connected_accounts_user_provider', 'connected_accounts',
                    ['user_id', 'provider'], unique=True)

    op.create_table(
        'career_graph_nodes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('node_type', sa.String(32), nullable=False),
        sa.Column('label', sa.String(256), nullable=False),
        sa.Column('canonical_id', sa.String(256), nullable=True),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('edges', postgresql.JSONB(), nullable=True),
        sa.Column('node_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_career_graph_nodes_user_id', 'career_graph_nodes', ['user_id'])
    op.create_index('idx_career_graph_nodes_user_type', 'career_graph_nodes', ['user_id', 'node_type'])
    op.create_index('idx_career_graph_nodes_canonical', 'career_graph_nodes', ['canonical_id'])


def downgrade() -> None:
    op.drop_table('career_graph_nodes')
    op.drop_table('connected_accounts')
    op.drop_table('evidence_items')
    op.drop_table('skills')
    op.drop_table('resume_documents')
