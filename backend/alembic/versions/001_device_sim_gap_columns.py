"""add device/sim security columns and gap_minutes

Revision ID: 001_device_sim_gap
Revises:
Create Date: 2025-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = '001_device_sim_gap'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Workers: SIM-change locking + device fingerprint
    op.add_column('workers', sa.Column('device_fingerprint', sa.String(200), nullable=True))
    op.add_column('workers', sa.Column('sim_hash', sa.String(64), nullable=True))
    op.add_column('workers', sa.Column('sim_changed_at', sa.DateTime(timezone=True), nullable=True))

    # Location pings: device-off gap tracking
    op.add_column('worker_location_pings', sa.Column('gap_minutes', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('workers', 'device_fingerprint')
    op.drop_column('workers', 'sim_hash')
    op.drop_column('workers', 'sim_changed_at')
    op.drop_column('worker_location_pings', 'gap_minutes')
