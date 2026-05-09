"""Phase 1: Data Infrastructure & Schema Expansion

- Add device tracking (device_id, device_hash, imei, device_model, first_seen_device_at)
- Add pincode granularity (pincode_6digit, pincode_3digit_zone, pincode_list)
- Add inactivity validation fields (app_inactivity_hours, gps_inactivity_hours)
- Create new tables: DeviceChange, PricingAudit, ClaimsMetrics, PincodeInfraScore, PincodeTriggerProbability, LossRatioDashboard
- Add HOLD_FOR_INACTIVITY_REVIEW status to claims

Revision ID: 20260505_001
Create Date: 2026-05-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260505_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    claimstatus_enum = postgresql.ENUM('pending', 'approved', 'rejected', 'paid', 'hold_for_inactivity_review', name='claimstatus')
    claimstatus_enum.create(op.get_bind())
    
    policytier_enum = postgresql.ENUM('basic', 'smart', 'pro', name='policytier')
    policytier_enum.create(op.get_bind())
    
    disruptiontype_enum = postgresql.ENUM('heavy_rain', 'extreme_heat', 'aqi_spike', 'traffic_disruption', 'civic_emergency', name='disruptiontype')
    disruptiontype_enum.create(op.get_bind())
    
    disruptionseverity_enum = postgresql.ENUM('moderate', 'severe', 'extreme', name='disruptionseverity')
    disruptionseverity_enum.create(op.get_bind())

    # ===== STEP 1: Update WORKERS table =====
    # Add device tracking columns
    op.add_column('workers', sa.Column('pincode_6digit', sa.String(6), nullable=True))
    op.add_column('workers', sa.Column('pincode_3digit_zone', sa.String(3), nullable=True))
    op.add_column('workers', sa.Column('device_id', sa.String(255), nullable=True))
    op.add_column('workers', sa.Column('device_hash', sa.String(64), nullable=True))
    op.add_column('workers', sa.Column('imei', sa.String(15), nullable=True))
    op.add_column('workers', sa.Column('device_model', sa.String(100), nullable=True))
    op.add_column('workers', sa.Column('first_seen_device_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('workers', sa.Column('last_known_device_id', sa.String(255), nullable=True))
    
    # Create indexes
    op.create_index('ix_workers_device_id', 'workers', ['device_id'])
    op.create_index('ix_workers_pincode_6digit', 'workers', ['pincode_6digit'])

    # ===== STEP 2: Update POLICIES table =====
    op.add_column('policies', sa.Column('pincode_6digit', sa.String(6), nullable=True))
    op.add_column('policies', sa.Column('pincode_3digit_zone', sa.String(3), nullable=True))
    op.create_index('ix_policies_pincode_6digit', 'policies', ['pincode_6digit'])

    # ===== STEP 3: Update DISRUPTION_EVENTS table =====
    op.add_column('disruption_events', sa.Column('pincode_6digit', sa.String(6), nullable=True))
    op.add_column('disruption_events', sa.Column('pincode_list', sa.Text, nullable=True))
    op.add_column('disruption_events', sa.Column('pincode_3digit_zone', sa.String(3), nullable=True))
    op.create_index('ix_disruption_events_pincode_6digit', 'disruption_events', ['pincode_6digit'])

    # ===== STEP 4: Update CLAIMS table =====
    # Add inactivity fields and update status enum
    op.execute("ALTER TYPE claimstatus ADD VALUE 'hold_for_inactivity_review'")
    op.add_column('claims', sa.Column('app_inactivity_hours', sa.Float, nullable=True))
    op.add_column('claims', sa.Column('gps_inactivity_hours', sa.Float, nullable=True))
    op.create_index('ix_claims_created_at', 'claims', ['created_at'])

    # ===== STEP 5: Create DEVICE_CHANGES table =====
    op.create_table('device_changes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('worker_id', sa.String(), nullable=False),
        sa.Column('old_device_hash', sa.String(64), nullable=True),
        sa.Column('old_device_id', sa.String(255), nullable=True),
        sa.Column('new_device_hash', sa.String(64), nullable=False),
        sa.Column('new_device_id', sa.String(255), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('fraud_flagged', sa.Boolean(), nullable=False, default=False),
        sa.Column('fraud_reason', sa.Text, nullable=True),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_device_changes_worker_id', 'device_changes', ['worker_id'])
    op.create_index('ix_device_changes_changed_at', 'device_changes', ['changed_at'])

    # ===== STEP 6: Create PRICING_AUDITS table =====
    op.create_table('pricing_audits',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('policy_id', sa.String(), nullable=False),
        sa.Column('previous_tier', sa.Enum('basic', 'smart', 'pro', name='policytier'), nullable=True),
        sa.Column('previous_premium', sa.Float(), nullable=True),
        sa.Column('new_tier', sa.Enum('basic', 'smart', 'pro', name='policytier'), nullable=False),
        sa.Column('new_premium', sa.Float(), nullable=False),
        sa.Column('recalc_reason', sa.String(50), nullable=False),
        sa.Column('claims_30day', sa.Integer(), nullable=True),
        sa.Column('payout_ratio_30day', sa.Float(), nullable=True),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pricing_audits_policy_id', 'pricing_audits', ['policy_id'])

    # ===== STEP 7: Create CLAIMS_METRICS table =====
    op.create_table('claims_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('worker_id', sa.String(), nullable=False),
        sa.Column('pincode', sa.String(6), nullable=True),
        sa.Column('pincode_3digit_zone', sa.String(3), nullable=True),
        sa.Column('claims_30day', sa.Integer(), nullable=False, default=0),
        sa.Column('payout_sum_30day', sa.Float(), nullable=False, default=0.0),
        sa.Column('premium_sum_30day', sa.Float(), nullable=False, default=0.0),
        sa.Column('payout_ratio_30day', sa.Float(), nullable=True),
        sa.Column('claims_90day', sa.Integer(), nullable=False, default=0),
        sa.Column('payout_sum_90day', sa.Float(), nullable=False, default=0.0),
        sa.Column('avg_payout_per_claim', sa.Float(), nullable=True),
        sa.Column('claims_per_week', sa.Float(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_claims_metrics_worker_id', 'claims_metrics', ['worker_id'])
    op.create_index('ix_claims_metrics_calculated_at', 'claims_metrics', ['calculated_at'])

    # ===== STEP 8: Create PINCODE_INFRA_SCORES table =====
    op.create_table('pincode_infra_scores',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('pincode_6digit', sa.String(6), nullable=False),
        sa.Column('pincode_3digit_zone', sa.String(3), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('infra_score', sa.Float(), nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pincode_6digit', name='uq_pincode_infra_scores_pincode_6digit')
    )
    op.create_index('ix_pincode_infra_scores_pincode_6digit', 'pincode_infra_scores', ['pincode_6digit'])
    op.create_index('ix_pincode_infra_scores_pincode_3digit_zone', 'pincode_infra_scores', ['pincode_3digit_zone'])

    # ===== STEP 9: Create PINCODE_TRIGGER_PROBABILITIES table =====
    op.create_table('pincode_trigger_probabilities',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('pincode_6digit', sa.String(6), nullable=False),
        sa.Column('pincode_3digit_zone', sa.String(3), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('disruption_type', sa.Enum('heavy_rain', 'extreme_heat', 'aqi_spike', 'traffic_disruption', 'civic_emergency', name='disruptiontype'), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False),
        sa.Column('historical_frequency', sa.Integer(), nullable=True),
        sa.Column('avg_severity', sa.Enum('moderate', 'severe', 'extreme', name='disruptionseverity'), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pincode_trigger_probabilities_pincode_6digit', 'pincode_trigger_probabilities', ['pincode_6digit'])

    # ===== STEP 10: Create LOSS_RATIO_DASHBOARD table =====
    op.create_table('loss_ratio_dashboard',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('aggregation_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('tier', sa.Enum('basic', 'smart', 'pro', name='policytier'), nullable=False),
        sa.Column('pincode_6digit', sa.String(6), nullable=True),
        sa.Column('pincode_3digit_zone', sa.String(3), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('policies_active', sa.Integer(), nullable=False, default=0),
        sa.Column('premiums_collected', sa.Float(), nullable=False, default=0.0),
        sa.Column('claims_submitted', sa.Integer(), nullable=False, default=0),
        sa.Column('claims_approved', sa.Integer(), nullable=False, default=0),
        sa.Column('claims_rejected', sa.Integer(), nullable=False, default=0),
        sa.Column('claims_paid', sa.Integer(), nullable=False, default=0),
        sa.Column('payouts_made', sa.Float(), nullable=False, default=0.0),
        sa.Column('loss_ratio', sa.Float(), nullable=True),
        sa.Column('avg_premium_per_worker', sa.Float(), nullable=True),
        sa.Column('avg_payout_per_claim', sa.Float(), nullable=True),
        sa.Column('claim_approval_rate', sa.Float(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_loss_ratio_dashboard_aggregation_date', 'loss_ratio_dashboard', ['aggregation_date'])
    op.create_index('ix_loss_ratio_dashboard_tier', 'loss_ratio_dashboard', ['tier'])
    op.create_index('ix_loss_ratio_dashboard_pincode_6digit', 'loss_ratio_dashboard', ['pincode_6digit'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('loss_ratio_dashboard')
    op.drop_table('pincode_trigger_probabilities')
    op.drop_table('pincode_infra_scores')
    op.drop_table('claims_metrics')
    op.drop_table('pricing_audits')
    op.drop_table('device_changes')

    # Drop columns from CLAIMS
    op.drop_column('claims', 'gps_inactivity_hours')
    op.drop_column('claims', 'app_inactivity_hours')

    # Drop columns from DISRUPTION_EVENTS
    op.drop_column('disruption_events', 'pincode_3digit_zone')
    op.drop_column('disruption_events', 'pincode_list')
    op.drop_column('disruption_events', 'pincode_6digit')

    # Drop columns from POLICIES
    op.drop_column('policies', 'pincode_3digit_zone')
    op.drop_column('policies', 'pincode_6digit')

    # Drop columns from WORKERS
    op.drop_column('workers', 'last_known_device_id')
    op.drop_column('workers', 'first_seen_device_at')
    op.drop_column('workers', 'device_model')
    op.drop_column('workers', 'imei')
    op.drop_column('workers', 'device_hash')
    op.drop_column('workers', 'device_id')
    op.drop_column('workers', 'pincode_3digit_zone')
    op.drop_column('workers', 'pincode_6digit')
