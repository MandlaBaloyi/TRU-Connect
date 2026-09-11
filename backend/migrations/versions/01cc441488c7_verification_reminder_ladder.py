"""Verification reminder ladder: stage + last-sent on supplier_profiles.

TWO COLUMNS, NOT A TABLE. The ladder is three rungs and the fact it
records -- "how far along the nudging are we, and when did it last
tick" -- is one-to-one with a supplier profile. A reminders table would
be a row per supplier with no second dimension to justify the join.

A STAGE COUNTER rather than the stock-order precedent's pair of
first_/second_reminder_sent_at columns: that ladder has two rungs and
this one has three, and a counter means a fourth costs no migration.

verification_reminder_sent_at DOUBLES AS THE CLOCK. Null means nothing
has been sent, and the job falls back to the profile's created_at --
which is why existing suppliers do not all receive three emails in the
first sweep after deploy.

Revision ID: 01cc441488c7
Revises: ca910c85ec11
"""
from alembic import op
import sqlalchemy as sa

revision = "01cc441488c7"
down_revision = "ca910c85ec11"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "supplier_profiles",
        sa.Column(
            "verification_reminder_stage",
            sa.SmallInteger(),
            nullable=False,
            server_default="0",
        ),
        schema="supplier",
    )
    op.add_column(
        "supplier_profiles",
        sa.Column(
            "verification_reminder_sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        schema="supplier",
    )


def downgrade():
    op.drop_column("supplier_profiles", "verification_reminder_sent_at", schema="supplier")
    op.drop_column("supplier_profiles", "verification_reminder_stage", schema="supplier")
