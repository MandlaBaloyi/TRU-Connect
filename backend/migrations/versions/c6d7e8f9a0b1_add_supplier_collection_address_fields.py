"""add supplier profile collection address fields

Revision ID: c6d7e8f9a0b1
Revises: b5c6d7e8f9a0
Create Date: 2026-09-04 20:00:00.000000

A supplier's own fixed premises, set once via the same map picker
StockOrder's delivery fields use -- structured address text plus real
coordinates. Deliberately separate from the existing `location`
column (general suburb/city, shown in wide un-connected search
results) -- see supplier_profiles.collection_* columns' own comment
for the full privacy reasoning: these are exposed only to businesses
with an active connection, same gate as whatsapp_number/contact_email.
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c6d7e8f9a0b1'
down_revision = 'b5c6d7e8f9a0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("supplier_profiles", sa.Column("collection_building", sa.Text(), nullable=True), schema="supplier")
    op.add_column("supplier_profiles", sa.Column("collection_street", sa.Text(), nullable=True), schema="supplier")
    op.add_column("supplier_profiles", sa.Column("collection_suburb", sa.Text(), nullable=True), schema="supplier")
    op.add_column("supplier_profiles", sa.Column("collection_city", sa.Text(), nullable=True), schema="supplier")
    op.add_column("supplier_profiles", sa.Column("collection_province", sa.Text(), nullable=True), schema="supplier")
    op.add_column("supplier_profiles", sa.Column("collection_postal_code", sa.Text(), nullable=True), schema="supplier")
    op.add_column(
        "supplier_profiles", sa.Column("collection_latitude", sa.Numeric(9, 6), nullable=True), schema="supplier"
    )
    op.add_column(
        "supplier_profiles", sa.Column("collection_longitude", sa.Numeric(9, 6), nullable=True), schema="supplier"
    )


def downgrade():
    op.drop_column("supplier_profiles", "collection_longitude", schema="supplier")
    op.drop_column("supplier_profiles", "collection_latitude", schema="supplier")
    op.drop_column("supplier_profiles", "collection_postal_code", schema="supplier")
    op.drop_column("supplier_profiles", "collection_province", schema="supplier")
    op.drop_column("supplier_profiles", "collection_city", schema="supplier")
    op.drop_column("supplier_profiles", "collection_suburb", schema="supplier")
    op.drop_column("supplier_profiles", "collection_street", schema="supplier")
    op.drop_column("supplier_profiles", "collection_building", schema="supplier")
