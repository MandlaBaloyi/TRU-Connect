"""Matching ladder: pg_trgm, brand aliases, match aliases, review queue

V2 step 6a. The FREE tiers of product matching -- barcode, learned
alias, normalised exact, and rules plus trigram. Nothing here calls a
model or costs anything to run, and none of it depends on the paid tier
ever being switched on.

pg_trgm IS A POSTGRES EXTENSION, not a Python dependency. It ships with
Postgres (1.6 on the 18.4 this project runs) and gives similarity() plus
a GIN index that turns "find the closest catalogue products" into an
index scan instead of a scan of every row. Without the index, tier 3
would get linearly slower with every product added -- the same "rank in
SQL, not Python" lesson the storefront ranking already records.

IT IS INSTALLED INTO THE catalogue SCHEMA, NOT public, AND THAT IS NOT
A STYLE CHOICE. This database HAS NO public SCHEMA -- search_path is
'"$user", public' and neither exists, so current_schema() is null and a
bare CREATE EXTENSION fails with "no schema has been selected to create
in". Found by the migration failing exactly that way.

The consequence is that everything from the extension must be
schema-qualified: catalogue.similarity(), catalogue.gin_trgm_ops, and
the similarity operator as OPERATOR(catalogue.%). Unqualified calls
resolve to nothing, because the schema is not on anyone's search_path.
See product_repository.search_similar, which does exactly that.

CREATE EXTENSION NEEDS ELEVATED RIGHTS on a managed database. If this
fails in production the fix is one grant, not a code change.

Revision ID: c32c5e454643
Revises: 38197be69f75
Create Date: 2026-09-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c32c5e454643"
down_revision = "38197be69f75"
branch_labels = None
depends_on = None


_ALIAS_SOURCE = postgresql.ENUM(
    "BARCODE", "HUMAN", "DECLARED",
    name="match_alias_source", schema="catalogue", create_type=False,
)
_REVIEW_STATUS = postgresql.ENUM(
    "PENDING", "AUTO_APPLIED", "ACCEPTED", "REJECTED",
    name="match_review_status", schema="catalogue", create_type=False,
)

#: All five BaseModel columns. Spelled out on every table because this
#: project has already shipped a migration that omitted deleted_at and
#: passed the whole suite -- conftest builds from model metadata and
#: never runs a migration, so tests cannot catch it.
def _base_columns():
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm SCHEMA catalogue")

    # THE INDEX THAT MAKES TIER 3 VIABLE. gin_trgm_ops is what lets
    # Postgres answer a similarity query without reading every product.
    op.execute(
        "CREATE INDEX ix_catalogue_products_normalized_name_trgm "
        "ON catalogue.products USING gin (normalized_name catalogue.gin_trgm_ops)"
    )

    op.create_table(
        "brand_aliases",
        *_base_columns(),
        sa.Column("alias_slug", sa.String(length=140), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["brand_id"], ["catalogue.brands.id"],
            name="fk_brand_aliases_brand_id", ondelete="CASCADE",
        ),
        sa.UniqueConstraint("alias_slug", name="uq_brand_aliases_alias_slug"),
        schema="catalogue",
    )
    op.create_index("ix_brand_aliases_brand_id", "brand_aliases", ["brand_id"], schema="catalogue")

    _ALIAS_SOURCE.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "match_aliases",
        *_base_columns(),
        sa.Column("matching_key", sa.String(length=200), nullable=False),
        sa.Column("source_text", sa.String(length=300), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", _ALIAS_SOURCE, nullable=False),
        sa.Column("times_seen", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.ForeignKeyConstraint(
            ["product_id"], ["catalogue.products.id"],
            name="fk_match_aliases_product_id", ondelete="CASCADE",
        ),
        sa.UniqueConstraint("matching_key", name="uq_match_aliases_matching_key"),
        schema="catalogue",
    )
    op.create_index("ix_match_aliases_product_id", "match_aliases", ["product_id"], schema="catalogue")

    _REVIEW_STATUS.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "match_reviews",
        *_base_columns(),
        sa.Column("supplier_offer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_text", sa.String(length=300), nullable=False),
        sa.Column("proposed_product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tier", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("reason", sa.String(length=300), nullable=False),
        sa.Column("status", _REVIEW_STATUS, nullable=False),
        sa.Column("decided_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        # SET NULL throughout: a decision's history must survive the
        # deletion of anything it refers to.
        sa.ForeignKeyConstraint(
            ["supplier_offer_id"], ["supplier.supplier_offers.id"],
            name="fk_match_reviews_supplier_offer_id", ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["proposed_product_id"], ["catalogue.products.id"],
            name="fk_match_reviews_proposed_product_id", ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["decided_by_user_id"], ["auth.users.id"],
            name="fk_match_reviews_decided_by_user_id",
        ),
        schema="catalogue",
    )
    op.create_index("ix_match_reviews_status", "match_reviews", ["status"], schema="catalogue")
    op.create_index(
        "ix_match_reviews_supplier_offer_id", "match_reviews", ["supplier_offer_id"], schema="catalogue"
    )


def downgrade():
    op.drop_table("match_reviews", schema="catalogue")
    _REVIEW_STATUS.drop(op.get_bind(), checkfirst=True)

    op.drop_table("match_aliases", schema="catalogue")
    _ALIAS_SOURCE.drop(op.get_bind(), checkfirst=True)

    op.drop_table("brand_aliases", schema="catalogue")

    op.execute("DROP INDEX IF EXISTS catalogue.ix_catalogue_products_normalized_name_trgm")
    # pg_trgm is deliberately NOT dropped. Another table may come to
    # depend on it, and an extension left installed costs nothing --
    # whereas dropping one out from under a live index is an outage.
