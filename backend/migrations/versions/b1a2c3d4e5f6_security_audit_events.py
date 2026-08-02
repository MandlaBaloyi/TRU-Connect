"""security audit_events table

Creates the single enterprise audit table in the `security` schema, its
indexes, and the append-only enforcement trigger.

APPEND-ONLY IS ENFORCED IN THE DATABASE, not just in application code. A
trigger rejects UPDATE and DELETE outright. Convention alone is only as
strong as the next service someone writes; regulators and investigations
depend on this being structurally true.

RETENTION NOTE: because DELETE is blocked, a future data-retention or
archival policy cannot simply delete old rows. It will need to disable
the trigger explicitly (ALTER TABLE ... DISABLE TRIGGER), archive, then
re-enable — a deliberately conspicuous operation that leaves a trace,
rather than something a stray query can do by accident.

Revision ID: b1a2c3d4e5f6
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b1a2c3d4e5f6"
down_revision = "acccb39c3c86"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS security")

    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("domain", sa.String(length=50), nullable=False),
        sa.Column("module", sa.String(length=100), nullable=True),
        sa.Column("event_name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("failure_reason", sa.String(length=255), nullable=True),
        sa.Column("actor_type", sa.String(length=30), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("browser", sa.String(length=50), nullable=True),
        sa.Column("operating_system", sa.String(length=50), nullable=True),
        sa.Column("platform", sa.String(length=30), nullable=True),
        sa.Column("device_id", sa.String(length=255), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("http_method", sa.String(length=10), nullable=True),
        sa.Column("endpoint", sa.String(length=255), nullable=True),
        sa.Column("http_status_code", sa.Integer(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="security",
    )

    # Indexes chosen for the queries the control center actually runs.
    # This table only grows, so an unindexed filter degrades permanently.
    op.create_index(
        "ix_audit_events_timestamp_desc", "audit_events",
        [sa.text("timestamp DESC")], schema="security",
    )
    op.create_index(
        "ix_audit_events_email_timestamp", "audit_events",
        ["email", sa.text("timestamp DESC")], schema="security",
    )
    op.create_index(
        "ix_audit_events_user_timestamp", "audit_events",
        ["user_id", sa.text("timestamp DESC")], schema="security",
    )
    op.create_index(
        "ix_audit_events_ip_timestamp", "audit_events",
        ["ip_address", sa.text("timestamp DESC")], schema="security",
    )
    op.create_index(
        "ix_audit_events_domain_event_timestamp", "audit_events",
        ["domain", "event_name", sa.text("timestamp DESC")], schema="security",
    )
    op.create_index(
        "ix_audit_events_correlation", "audit_events",
        ["correlation_id"], schema="security",
    )
    op.create_index(
        "ix_audit_events_tenant_timestamp", "audit_events",
        ["tenant_id", sa.text("timestamp DESC")], schema="security",
    )

    # Append-only enforcement.
    op.execute("""
        CREATE OR REPLACE FUNCTION security.reject_audit_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION
                'audit_events is append-only: % is not permitted', TG_OP
                USING HINT = 'Audit records are immutable for compliance. '
                             'To archive, disable this trigger explicitly.';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_audit_events_append_only
        BEFORE UPDATE OR DELETE ON security.audit_events
        FOR EACH ROW EXECUTE FUNCTION security.reject_audit_mutation();
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_audit_events_append_only ON security.audit_events")
    op.execute("DROP FUNCTION IF EXISTS security.reject_audit_mutation()")
    for name in (
        "ix_audit_events_tenant_timestamp",
        "ix_audit_events_correlation",
        "ix_audit_events_domain_event_timestamp",
        "ix_audit_events_ip_timestamp",
        "ix_audit_events_user_timestamp",
        "ix_audit_events_email_timestamp",
        "ix_audit_events_timestamp_desc",
    ):
        op.drop_index(name, table_name="audit_events", schema="security")
    op.drop_table("audit_events", schema="security")
