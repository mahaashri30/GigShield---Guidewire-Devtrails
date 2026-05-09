"""add soft delete and deleted_account_archives

Revision ID: 002_soft_delete
Revises: 001_device_sim_gap
Create Date: 2025-01-01 00:00:01
"""
from alembic import op
import sqlalchemy as sa

revision = '002_soft_delete'
down_revision = '001_device_sim_gap'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Soft delete fields on workers
    op.add_column('workers', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('workers', sa.Column('deletion_requested_at', sa.DateTime(timezone=True), nullable=True))

    # Archive table for deleted accounts
    op.create_table(
        'deleted_account_archives',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('original_worker_id', sa.String(), nullable=False, index=True),
        sa.Column('phone_hash', sa.String(64), nullable=False),
        sa.Column('name_redacted', sa.String(20), nullable=False),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('platform', sa.String(50), nullable=True),
        sa.Column('total_policies', sa.Integer(), default=0),
        sa.Column('total_claims', sa.Integer(), default=0),
        sa.Column('total_premium_paid', sa.Float(), default=0.0),
        sa.Column('total_claims_paid', sa.Float(), default=0.0),
        sa.Column('deletion_requested_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deletion_reason', sa.String(200), nullable=True),
        sa.Column('grace_period_ends_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('permanently_purged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('deleted_account_archives')
    op.drop_column('workers', 'is_deleted')
    op.drop_column('workers', 'deletion_requested_at')
