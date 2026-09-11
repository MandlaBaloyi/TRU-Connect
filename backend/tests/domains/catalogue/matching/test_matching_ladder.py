"""
The matching ladder, rung by rung.

EVERY TEST HERE RUNS FOR FREE. No network, no model, no API key -- which
is the whole claim of step 6a: the deterministic tiers work with the
paid tier switched off forever, and turning it off is the default.

THE ORDER OF THE RUNGS IS THE COST STRATEGY, so several tests assert not
just that a match was found but WHICH tier found it. A barcode match
that quietly came from fuzzy text would still be correct today and would
still mean the cheap path had silently stopped working.
"""
from __future__ import annotations

import pytest

from src.domains.catalogue.matching.algorithms.confidence import MatchDecision, MatchTier
from src.domains.catalogue.matching.algorithms.normalise import matching_key
from src.domains.catalogue.matching.algorithms.pack_size import PackSize
from src.domains.catalogue.matching.models.match_alias import AliasSource
from src.domains.catalogue.matching.repositories.match_alias_repository import (
    MatchAliasRepository,
)
from src.domains.catalogue.matching.services import matching_service
from src.domains.catalogue.products.models.brand import Brand
from src.domains.catalogue.products.models.product import Product
from src.domains.catalogue.products.models.taxonomy import ProductCategory, ProductUnit
from src.domains.catalogue.products.repositories.brand_repository import BrandRepository
from src.extensions import db


def _product(
    name: str,
    *,
    normalized: str | None = None,
    gtin: str | None = None,
    brand_id=None,
    quantity: int | None = None,
    measure: ProductUnit | None = None,
) -> Product:
    from src.domains.catalogue.matching.algorithms.normalise import normalise_text

    product = Product(
        name=name,
        normalized_name=normalized or normalise_text(name),
        category=ProductCategory.BEVERAGES,
        gtin=gtin,
        brand_id=brand_id,
        unit_quantity=quantity,
        unit_measure=measure,
    )
    db.session.add(product)
    db.session.flush()
    return product


# --- tier 0: barcode -------------------------------------------------------


def test_a_barcode_matches_exactly_and_costs_nothing(db_session):
    product = _product("Coca-Cola Original 2L", gtin="5449000054227")

    proposal = matching_service.propose_match(
        name="SOMETHING COMPLETELY UNLIKE THE CATALOGUE NAME",
        barcode="5449000054227",
    )

    assert proposal.product_id == product.id
    assert proposal.tier is MatchTier.BARCODE
    assert proposal.confidence == 1.0
    assert proposal.decision is MatchDecision.AUTO_LINK


def test_a_barcode_that_matches_nothing_falls_through_rather_than_failing(db_session):
    _product("Coca-Cola Original 2L")
    proposal = matching_service.propose_match(name="Coca-Cola Original 2L", barcode="0000000000000")
    assert proposal.tier is not MatchTier.BARCODE


# --- tier 1: learned alias -------------------------------------------------


def test_a_confirmed_alias_answers_instantly(db_session):
    """The rung that compounds. One supplier's confirmed match answers
    the same text for everyone who writes it afterwards, free."""
    product = _product("Coca-Cola Original 2L")
    MatchAliasRepository.upsert(
        matching_key=matching_key("COKE 2LT PET 6PK"),
        source_text="COKE 2LT PET 6PK",
        product_id=product.id,
        source=AliasSource.HUMAN,
    )
    db.session.flush()

    proposal = matching_service.propose_match(name="COKE 2LT PET 6PK")

    assert proposal.product_id == product.id
    assert proposal.tier is MatchTier.ALIAS
    assert proposal.decision is MatchDecision.AUTO_LINK


def test_an_alias_hit_is_counted(db_session):
    """times_seen is how you find out which aliases are worth a human's
    attention and which are stale enough to remove."""
    product = _product("Coca-Cola Original 2L")
    alias = MatchAliasRepository.upsert(
        matching_key=matching_key("COKE 2LT"),
        source_text="COKE 2LT",
        product_id=product.id,
        source=AliasSource.HUMAN,
    )
    db.session.flush()
    assert alias.times_seen == 1

    matching_service.propose_match(name="COKE 2LT")
    assert alias.times_seen == 2


def test_an_alias_is_never_silently_repointed_at_a_different_product(db_session):
    """One text means one product. A contradiction is something a person
    should see, not something a background import resolves by
    overwriting."""
    first = _product("Coca-Cola Original 2L")
    second = _product("Fanta Orange 2L", normalized="fanta orange 2l")

    key = matching_key("COKE 2LT")
    MatchAliasRepository.upsert(
        matching_key=key, source_text="COKE 2LT", product_id=first.id, source=AliasSource.HUMAN
    )
    db.session.flush()
    MatchAliasRepository.upsert(
        matching_key=key, source_text="COKE 2LT", product_id=second.id, source=AliasSource.HUMAN
    )
    db.session.flush()

    assert MatchAliasRepository.get(key).product_id == first.id


# --- tier 2: same words, any order ----------------------------------------


def test_word_order_alone_does_not_prevent_a_match(db_session):
    product = _product("Coca-Cola Original 2L")

    proposal = matching_service.propose_match(name="2L Original Coca Cola")

    assert proposal.product_id == product.id
    assert proposal.tier is MatchTier.NORMALISED
    assert proposal.decision is MatchDecision.AUTO_LINK


# --- tier 3: brand, pack and fuzzy text -----------------------------------


def test_a_close_description_is_proposed_with_a_real_score(db_session):
    product = _product(
        "Coca-Cola Original 2 Litre", quantity=2, measure=ProductUnit.L
    )

    proposal = matching_service.propose_match(name="Coca Cola Original 2L bottle")

    assert proposal.product_id == product.id
    assert proposal.tier is MatchTier.RULES
    assert 0 < proposal.confidence <= 1


def test_a_different_pack_size_is_not_the_same_product(db_session):
    """THE MOST DANGEROUS CASE. These read almost identically as text and
    are absolutely not the same thing -- linking them would put a
    per-unit price on a card that is out by a factor of four."""
    _product("Coca-Cola Original 500ml", quantity=500, measure=ProductUnit.ML)

    proposal = matching_service.propose_match(
        name="Coca-Cola Original 2L",
        pack=PackSize(unit_quantity=2, unit_measure="L"),
    )

    assert proposal.decision is not MatchDecision.AUTO_LINK
    assert "DIFFERENT pack size" in proposal.reason


def test_two_litres_and_two_thousand_millilitres_are_the_same_pack(db_session):
    """to_base earning its place at the database boundary, not just in
    the unit tests."""
    _product("Coca-Cola Original 2000ml", quantity=2000, measure=ProductUnit.ML)

    proposal = matching_service.propose_match(
        name="Coca-Cola Original 2000ml",
        pack=PackSize(unit_quantity=2, unit_measure="L"),
    )

    assert "DIFFERENT pack size" not in proposal.reason


def test_a_brand_alias_resolves_what_suppliers_actually_write(db_session):
    """"COKE" and "cocacola" share almost no character triples, so
    trigram similarity cannot save you here. This is why the alias table
    is a lookup rather than an algorithm."""
    brand = BrandRepository.get_or_create("Coca-Cola", "cocacola")
    BrandRepository.add_alias(brand.id, "coke")
    db.session.flush()

    assert BrandRepository.resolve("coke").id == brand.id
    assert BrandRepository.resolve("cocacola").id == brand.id
    assert BrandRepository.resolve("pepsi") is None


def test_a_real_brand_name_is_never_shadowed_by_a_careless_alias(db_session):
    """The canonical slug is checked first, so adding a bad alias cannot
    hijack an existing brand."""
    real = BrandRepository.get_or_create("Fanta", "fanta")
    other = BrandRepository.get_or_create("Coca-Cola", "cocacola")
    BrandRepository.add_alias(other.id, "fanta")  # careless
    db.session.flush()

    assert BrandRepository.resolve("fanta").id == real.id


# --- nothing found ---------------------------------------------------------


def test_nothing_plausible_means_create_a_new_product(db_session):
    _product("Coca-Cola Original 2L")

    proposal = matching_service.propose_match(name="Galvanised Roofing Nails 4 inch")

    assert proposal.product_id is None
    assert proposal.confidence == 0.0
    assert proposal.decision is MatchDecision.CREATE_NEW


def test_an_empty_catalogue_proposes_nothing_rather_than_failing(db_session):
    proposal = matching_service.propose_match(name="Coca-Cola Original 2L")
    assert proposal.product_id is None
    assert proposal.decision is MatchDecision.CREATE_NEW


# --- the switches ----------------------------------------------------------


def test_the_kill_switch_stops_matching_without_breaking_anything(db_session, monkeypatch):
    """Off means offers stay unmatched -- exactly how every offer behaves
    today. A no-deploy way to stop matching platform-wide, mirroring
    BULK_IMPORT_ENABLED."""
    product = _product("Coca-Cola Original 2L", gtin="5449000054227")
    monkeypatch.setenv("MATCHING_ENABLED", "false")

    proposal = matching_service.propose_match(
        name="Coca-Cola Original 2L", barcode="5449000054227"
    )

    assert proposal.product_id is None
    assert proposal.decision is MatchDecision.CREATE_NEW
    assert product.id is not None  # the catalogue itself is untouched


def test_the_paid_tier_is_off_by_default(monkeypatch):
    """Three independent things must agree before a paid call is made,
    and this is the first of them. The default is free."""
    from src.domains.catalogue.matching.config import matching_config

    monkeypatch.delenv("MATCHING_MODE", raising=False)
    assert matching_config.use_ai_tier() is False


# --- tier 0: the barcode consistency check ---------------------------------
#
# A GTIN names exactly one trade item, so tier 0 returns 1.0 and the
# words "matches this product exactly". That is what makes a WRONG
# barcode dangerous rather than merely unhelpful: it is not a near miss,
# it is a confident link to a different real product that nobody
# reviews. See _barcode_contradiction for why only the STRUCTURED
# signals are used and why text was measured and rejected.


def test_a_barcode_whose_pack_size_disagrees_goes_to_review(db_session):
    """THE CASE THAT COSTS REAL MONEY. "Coke 2L" and "Coke 500ml" read
    almost identically as text; linking them puts a per-unit price on a
    card that is out by a factor of four."""
    from src.domains.catalogue.matching.algorithms.pack_size import PackSize

    product = _product(
        "Coca-Cola Original 2L", gtin="5449000054227", quantity=2, measure=ProductUnit.L
    )

    proposal = matching_service.propose_match(
        name="Coca-Cola Original 500ml",
        barcode="5449000054227",
        # UPPERCASE, matching ProductUnit's name==value convention -- it is
        # what every real caller passes (linking_service sends
        # unit_measure.value), and _BASE_FACTORS is keyed that way.
        pack=PackSize(unit_quantity=500, unit_measure="ML"),
    )

    assert proposal.product_id == product.id, "the barcode still identifies a candidate"
    assert proposal.contradicted is True
    assert proposal.decision is MatchDecision.REVIEW, "must NOT auto-link"
    assert "pack size" in proposal.reason


def test_a_barcode_whose_brand_disagrees_goes_to_review(db_session):
    """A supplier typing the cooldrink's barcode onto a juice. The
    number is valid; it is on the wrong product."""
    coke = BrandRepository.get_or_create("Coca-Cola", "cocacola")
    BrandRepository.get_or_create("Liqui Fruit", "liquifruit")
    product = _product(
        "Coca-Cola Original 2L", gtin="5449000054227", brand_id=coke.id,
        quantity=2, measure=ProductUnit.L,
    )

    proposal = matching_service.propose_match(
        name="Liqui Fruit Orange 2L",
        barcode="5449000054227",
        brand="Liqui Fruit",
    )

    assert proposal.product_id == product.id
    assert proposal.contradicted is True
    assert proposal.decision is MatchDecision.REVIEW
    assert "brand" in proposal.reason


def test_a_barcode_with_agreeing_evidence_still_auto_links(db_session):
    """The check must not cost the 99% anything."""
    from src.domains.catalogue.matching.algorithms.pack_size import PackSize

    coke = BrandRepository.get_or_create("Coca-Cola", "cocacola")
    product = _product(
        "Coca-Cola Original 2L", gtin="5449000054227", brand_id=coke.id,
        quantity=2, measure=ProductUnit.L,
    )

    proposal = matching_service.propose_match(
        name="COKE 2LT PET",
        barcode="5449000054227",
        brand="Coca-Cola",
        pack=PackSize(unit_quantity=2, unit_measure="L"),
    )

    assert proposal.product_id == product.id
    assert proposal.contradicted is False
    assert proposal.decision is MatchDecision.AUTO_LINK


def test_a_barcode_with_nothing_to_contradict_it_still_auto_links(db_session):
    """NONE IS NOT DISAGREEMENT. A row with no brand column and no
    parseable pack size says nothing against the barcode, and a barcode
    with nothing against it is still the best identifier there is."""
    product = _product("Coca-Cola Original 2L", gtin="5449000054227")

    proposal = matching_service.propose_match(
        name="SOMETHING COMPLETELY UNLIKE THE CATALOGUE NAME",
        barcode="5449000054227",
    )

    assert proposal.product_id == product.id
    assert proposal.contradicted is False
    assert proposal.decision is MatchDecision.AUTO_LINK
