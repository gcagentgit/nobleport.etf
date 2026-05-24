"""Matter OS Foundation — RAOS, PermitStream, AuditBeacon, Agent Mesh

Revision ID: 002_matter_os
Revises: 001_add_revenue_tables
Create Date: 2026-05-24
"""

from alembic import op
import sqlalchemy as sa

revision = "002_matter_os"
down_revision = "001_add_revenue_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Permits (PermitStream) ──────────────────────────────────────
    op.create_table(
        "permits",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("jobs.id"), nullable=True, index=True),
        sa.Column("lead_id", sa.String(36), sa.ForeignKey("leads.id"), nullable=True, index=True),
        sa.Column("permit_number", sa.String(100), nullable=True, unique=True),
        sa.Column("internal_ref", sa.String(50), nullable=False, unique=True),
        sa.Column("permit_type", sa.String(20), nullable=False, server_default="building"),
        sa.Column("status", sa.String(20), nullable=False, server_default="intake"),
        sa.Column("ahj", sa.String(255), nullable=False),
        sa.Column("ahj_contact", sa.String(255), nullable=True),
        sa.Column("ahj_phone", sa.String(50), nullable=True),
        sa.Column("property_address", sa.String(500), nullable=False),
        sa.Column("parcel_id", sa.String(100), nullable=True),
        sa.Column("zoning_district", sa.String(100), nullable=True),
        sa.Column("project_description", sa.Text, nullable=True),
        sa.Column("scope_type", sa.String(100), nullable=True),
        sa.Column("estimated_cost", sa.Float, nullable=False, server_default="0"),
        sa.Column("square_footage", sa.Float, nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deficiency_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("zoning_risk_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("completeness_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("forecast_days_to_issue", sa.Integer, nullable=True),
        sa.Column("deficiency_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("correction_rounds", sa.Integer, nullable=False, server_default="0"),
        sa.Column("zoning_flags", sa.Text, nullable=True),
        sa.Column("checklist_json", sa.Text, nullable=True),
        sa.Column("reviewer", sa.String(255), nullable=True),
        sa.Column("assigned_agent", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── Audit Entries (AuditBeacon) ─────────────────────────────────
    op.create_table(
        "audit_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("operator", sa.String(255), nullable=False),
        sa.Column("agent", sa.String(100), nullable=True),
        sa.Column("action", sa.String(20), nullable=False, index=True),
        sa.Column("subject_type", sa.String(100), nullable=False, index=True),
        sa.Column("subject_id", sa.String(36), nullable=False, index=True),
        sa.Column("subject_label", sa.String(500), nullable=True),
        sa.Column("approval", sa.String(20), nullable=False, server_default="auto"),
        sa.Column("entry_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("prev_hash", sa.String(64), nullable=False),
        sa.Column("anchor_tx", sa.String(66), nullable=True),
        sa.Column("anchor_chain", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="committed"),
        sa.Column("detail", sa.Text, nullable=True),
        sa.Column("metadata_json", sa.Text, nullable=True),
        sa.Column("verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── Registered Agents (Agent Mesh) ──────────────────────────────
    op.create_table(
        "registered_agents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("family", sa.String(20), nullable=False, index=True),
        sa.Column("role", sa.String(500), nullable=False),
        sa.Column("version", sa.String(50), nullable=False, server_default="1.0.0"),
        sa.Column("health", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("queue_depth", sa.Integer, nullable=False, server_default="0"),
        sa.Column("in_flight", sa.Integer, nullable=False, server_default="0"),
        sa.Column("p95_latency_ms", sa.Float, nullable=False, server_default="0"),
        sa.Column("error_rate", sa.Float, nullable=False, server_default="0"),
        sa.Column("uptime_30d", sa.Float, nullable=False, server_default="100"),
        sa.Column("tasks_completed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
        sa.Column("kill_switch_armed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("kill_switch_scope", sa.String(255), nullable=True),
        sa.Column("current_task", sa.String(500), nullable=True),
        sa.Column("config_json", sa.Text, nullable=True),
        sa.Column("capabilities_json", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── Notifications ───────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("channel", sa.String(20), nullable=False, index=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("category", sa.String(20), nullable=False, index=True),
        sa.Column("recipient", sa.String(255), nullable=False, index=True),
        sa.Column("sender", sa.String(255), nullable=False),
        sa.Column("agent", sa.String(100), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("subject_type", sa.String(100), nullable=True),
        sa.Column("subject_id", sa.String(36), nullable=True),
        sa.Column("read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("action_url", sa.String(500), nullable=True),
        sa.Column("metadata_json", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── Operational Memory (RAOS) ───────────────────────────────────
    op.create_table(
        "operational_memory",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scope", sa.String(20), nullable=False, index=True),
        sa.Column("category", sa.String(30), nullable=False, index=True),
        sa.Column("key", sa.String(500), nullable=False, index=True),
        sa.Column("value_json", sa.Text, nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True, index=True),
        sa.Column("entity_id", sa.String(36), nullable=True, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("written_by", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("operational_memory")
    op.drop_table("notifications")
    op.drop_table("registered_agents")
    op.drop_table("audit_entries")
    op.drop_table("permits")
