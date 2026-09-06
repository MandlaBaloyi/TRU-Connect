"""add stock order delivery location fields

Revision ID: b5c6d7e8f9a0
Revises: a3b4c5d6e7f8
Create Date: 2026-09-04 09:00:00.000000

Structured delivery-address components plus real coordinates,
alongside the existing delivery_address_text (which stays exactly as
it is -- the composed, human-readable snapshot every existing caller
already reads). All nullable, same historical-snapshot reasoning
delivery_address_text's own column comment already gives: a business's
address today shouldn't silently rewrite what a past order says it
was delivered to.

delivery_latitude/delivery_longitude are never populated from a
Mapbox geocoding response -- they're the real coordinates of the pin
the business dragged the map to, captured by the frontend's map
widget directly (see src/domains/network/geocoding's own module
docstring for why that distinction matters for Mapbox's storage
terms). delivery_building/_street/_suburb/_city/_province/_postal_code
are the business's own confirmed/edited text, pre-filled from a
reverse-geocode lookup but never stored as Mapbox's raw response.

Kept as separate columns rather than only ever living inside
delivery_address_text's composed string -- the explicitly-flagged
future use (nearest-supplier / nearest-business recommendations, per
direct discussion) needs city/province/coordinates addressable on
their own, not re-parsed out of free text.
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b5c6d7e8f9a0'
down_revision = 'a3b4c5d6e7f8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("stock_orders", sa.Column("delivery_building", sa.Text(), nullable=True), schema="checkout")
    op.add_column("stock_orders", sa.Column("delivery_street", sa.Text(), nullable=True), schema="checkout")
    op.add_column("stock_orders", sa.Column("delivery_suburb", sa.Text(), nullable=True), schema="checkout")
    op.add_column("stock_orders", sa.Column("delivery_city", sa.Text(), nullable=True), schema="checkout")
    op.add_column("stock_orders", sa.Column("delivery_province", sa.Text(), nullable=True), schema="checkout")
    op.add_column("stock_orders", sa.Column("delivery_postal_code", sa.Text(), nullable=True), schema="checkout")
    # Numeric, not Float -- exact decimal storage, no floating-point
    # drift on repeated reads/writes. 9 total digits, 6 after the
    # decimal point: matches standard GPS precision (~11cm at the
    # equator), comfortably more than this feature needs, and covers
    # the full -180..180 / -90..90 range with room to spare.
    op.add_column("stock_orders", sa.Column("delivery_latitude", sa.Numeric(9, 6), nullable=True), schema="checkout")
    op.add_column("stock_orders", sa.Column("delivery_longitude", sa.Numeric(9, 6), nullable=True), schema="checkout")


def downgrade():
    op.drop_column("stock_orders", "delivery_longitude", schema="checkout")
    op.drop_column("stock_orders", "delivery_latitude", schema="checkout")
    op.drop_column("stock_orders", "delivery_postal_code", schema="checkout")
    op.drop_column("stock_orders", "delivery_province", schema="checkout")
    op.drop_column("stock_orders", "delivery_city", schema="checkout")
    op.drop_column("stock_orders", "delivery_suburb", schema="checkout")
    op.drop_column("stock_orders", "delivery_street", schema="checkout")
    op.drop_column("stock_orders", "delivery_building", schema="checkout")
