"""
Brand -- "Coca-Cola", "Sunlight", "Koo".

A REAL TABLE RATHER THAN A STRING COLUMN ON Product, decided up front
because the migration away from a string is the expensive one. Two
things need brands to be entities:

1. MATCHING. Candidate search for "COKE 2LT PET 6PK" narrows by brand
   before it compares names. A free-text column gives you "Coca-Cola",
   "Coca Cola", "COCA-COLA" and "Coke" as four different brands, which
   is exactly the noise the matcher exists to remove.

2. THE IMAGE CASCADE (V2_00 section 2.8). A tile resolves
   offer image -> product image -> BRAND MARK -> category image, and
   never renders blank. Roughly 200 marks cover most of South African
   FMCG, which makes this the highest-leverage image tier: small files,
   a low quality bar, and a far more comfortable licensing position than
   product photography, since using a brand's mark to identify genuine
   goods you actually sell is ordinary trademark practice.

NOTHING READS THIS YET. The catalogue arrives dormant on purpose -- see
the Product model's docstring.
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class Brand(BaseModel):
    __tablename__ = "brands"
    __table_args__ = ({"schema": "catalogue"},)

    #: As it should be shown to a human: "Coca-Cola".
    name = db.Column(db.String(120), nullable=False)

    #: The matching key: lowercased, punctuation and spacing stripped
    #: ("coca-cola" and "Coca Cola" both normalise to "cocacola").
    #: UNIQUE, so the same brand cannot be created twice under different
    #: spellings -- which is the entire reason this table exists rather
    #: than a text column.
    slug = db.Column(db.String(140), nullable=False, unique=True)

    #: Tier 2 of the image cascade. Nullable, and normal to be null: a
    #: brand is usable the moment it has a name.
    mark_url = db.Column(db.String(500), nullable=True)


class BrandAlias(BaseModel):
    """What suppliers actually call a brand.

    "COKE" is not Coca-Cola's name, but it is what half of South Africa
    writes on an invoice. Trigram similarity does not save you here --
    "coke" and "cocacola" share almost no character triples -- so this is
    a lookup table, not a clever algorithm.

    SMALL AND HAND-CURATED ON PURPOSE. A few hundred rows covers most of
    SA FMCG, and every row added removes work from the paid tier
    permanently. This is the cheapest place in the whole system to buy
    accuracy: one insert, and every supplier who writes "OMO" from then
    on resolves for free.

    NOT inferred automatically. An alias created from a guess would make
    every future match inherit that guess, and unlike a single wrong
    product match it would be wrong across the whole catalogue.
    """

    __tablename__ = "brand_aliases"
    __table_args__ = (
        db.Index("ix_brand_aliases_brand_id", "brand_id"),
        # One alias cannot mean two brands. "COKE" resolves to exactly
        # one thing or it is useless as a narrowing signal.
        db.UniqueConstraint("alias_slug", name="uq_brand_aliases_alias_slug"),
        {"schema": "catalogue"},
    )

    #: normalise.brand_slug() of what the supplier wrote: "coke".
    alias_slug = db.Column(db.String(140), nullable=False)

    brand_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("catalogue.brands.id", ondelete="CASCADE"),
        nullable=False,
    )
