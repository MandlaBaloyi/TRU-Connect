"""
network_invitation_fk_set_null

Revision ID: 2ea418343d1b
Revises: 6c44aff745a7
Create Date: 2026-08-14

VERIFY BEFORE RUNNING: down_revision assumes 6c44aff745a7
(network_invitation_generalization) is your current head.

REAL BUG FIX, found while building the expired-invitation cleanup job,
not a cosmetic change: network_invitations.invited_user_id had a plain
FK to auth.users.id with no ON DELETE behaviour (Postgres default:
NO ACTION). The EXISTING auth cleanup job
(auth/jobs/cleanup_unverified_emails.py) hard-deletes unverified
accounts after UNVERIFIED_EMAIL_CLEANUP_DAYS -- which is exactly 7
days, the SAME as the invitation ticket's own default expiry
(DEFAULT_SUPPLIER_INVITATION_EXPIRY_HOURS = 168 hours). Anyone who
registered via a real invitation link and never verified their email
would hit both thresholds at close to the same time -- and the
account-cleanup job's bulk DELETE would fail outright with a foreign
key violation the moment it tried to delete a user still referenced by
an invitation, silently breaking that entire cleanup run, not just
skipping the one row.

FIX: ON DELETE SET NULL. invited_user_id is already nullable -- when
the referenced user is deleted, this column just becomes NULL instead
of blocking the delete. The invitation row survives (still useful
audit trail: "someone registered with this ticket, but the account
never got verified and was cleaned up"), it just loses the link to an
account that no longer exists.

Constraint name kept from the original migration
(supplier_invitations_invited_user_id_fkey) -- PostgreSQL doesn't
rename constraints when a table itself is renamed (confirmed directly
against the live schema), so this is genuinely the correct name to
target, not a leftover to "fix" separately.
"""
from alembic import op

revision = "2ea418343d1b"
down_revision = "6c44aff745a7"  # VERIFY -- see docstring above
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "supplier_invitations_invited_user_id_fkey", "network_invitations", schema="network", type_="foreignkey"
    )
    op.create_foreign_key(
        "supplier_invitations_invited_user_id_fkey",
        "network_invitations",
        "users",
        ["invited_user_id"],
        ["id"],
        source_schema="network",
        referent_schema="auth",
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(
        "supplier_invitations_invited_user_id_fkey", "network_invitations", schema="network", type_="foreignkey"
    )
    op.create_foreign_key(
        "supplier_invitations_invited_user_id_fkey",
        "network_invitations",
        "users",
        ["invited_user_id"],
        ["id"],
        source_schema="network",
        referent_schema="auth",
    )
