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
