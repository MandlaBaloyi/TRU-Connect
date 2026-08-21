"""widen product_media.scan_result to text

Revision ID: 7d3f9c2b8e41
Revises: 5b8f3d2a9c17
Create Date: 2026-08-21 20:20:00.000000

Found during real device testing: the VARCHAR(500) cap was exceeded
by a genuine Cloudinary webhook payload (its own nested
notification_context/triggered_by fields push a stringified payload
past 500 characters), crashing the webhook handler with a real
StringDataRightTruncation error. This is diagnostic/audit data with
no real reason to have an arbitrary length cap.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7d3f9c2b8e41'
down_revision = '5b8f3d2a9c17'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "product_media",
        "scan_result",
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        schema="supplier",
    )


def downgrade():
    # Reverting to VARCHAR(500) after real payloads may have already
    # been stored past that length would itself fail -- explicit,
    # honest failure rather than silently truncating real data.
    op.alter_column(
        "product_media",
        "scan_result",
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        schema="supplier",
    )
