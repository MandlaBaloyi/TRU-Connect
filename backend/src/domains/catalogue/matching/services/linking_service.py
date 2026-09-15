"""
Acting on a proposal: link it, queue it, or create a new catalogue
product.

SEPARATE FROM matching_service ON PURPOSE. That module answers "which
product is this, and how sure am I"; this one answers "what are we
allowed to do about it". Keeping the question apart from the consequence
is what lets the confidence gate be the only place a decision is made,
and what makes a cheaper model safe -- it changes the first answer, never
this file's rules.

EVERY OUTCOME IS RECORDED, including the confident ones. An auto-link
writes an AUTO_APPLIED review row, not because anyone needs to look at
it, but because a supplier disputing a match is owed an answer: which
tier proposed it, at what confidence, on what text. A link nobody can
explain is a link nobody can defend.

CREATE_NEW IS HOW THE CATALOGUE FILLS UP. Nobody sits down and types a
product catalogue; it accumulates as suppliers join. The first supplier
to send "Coca-Cola Original 2L" creates the entry and everyone after
matches to it. That is the whole bootstrap, and it is why a low
confidence is a normal outcome rather than a failure.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Optional

from src.domains.catalogue.matching.algorithms import gtin, normalise
from src.domains.catalogue.matching.algorithms.confidence import (
    MatchDecision,
    MatchProposal,
    MatchTier,
)
from src.domains.catalogue.matching.algorithms.pack_size import PackSize, resolve_pack
from src.domains.catalogue.matching.config import matching_config
from src.domains.catalogue.matching.models.match_alias import AliasSource
from src.domains.catalogue.matching.models.match_review import ReviewStatus
from src.domains.catalogue.matching.repositories.match_alias_repository import (
    MatchAliasRepository,
)
from src.domains.catalogue.matching.repositories.match_review_repository import (
    MatchReviewRepository,
)
from src.domains.catalogue.matching.services import matching_service
from src.domains.catalogue.products.models.taxonomy import ProductCategory, ProductUnit
from src.domains.catalogue.products.repositories.brand_repository import BrandRepository
from src.domains.catalogue.products.repositories.product_repository import (
    CatalogueProductRepository,
)


def match_fingerprint(
    *,
    name: str,
    barcode: Optional[str],
    brand: Optional[str],
    unit_quantity: Optional[int],
    unit_measure: Optional[ProductUnit],
) -> str:
    """A stable hash of everything matching is given.

    THE INPUTS, NOT THE ANSWER. If these are identical to last time, the
    answer is identical to last time, and re-deriving it is pure waste.

    NORMALISED BEFORE HASHING, so that "Coke 2L" and " coke  2l " -- the
    same product typed with different whitespace or case -- do not look
    like a change and trigger a pointless re-match.

    SHA-256 over a delimited string, and the delimiter matters: without
    it, ("ab", "c") and ("a", "bc") hash the same, so a brand ending in
    a character the name began with could hide a real change.
    """
    parts = [
        normalise.normalise_text(name or ""),
        (barcode or "").strip(),
        normalise.brand_slug(brand) if brand else "",
        str(unit_quantity) if unit_quantity is not None else "",
        unit_measure.value if unit_measure else "",
    ]
    return hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MatchOutcome:
    """What happened, in terms the import report can print."""

    decision: MatchDecision
    tier: MatchTier
    confidence: float
    product_id: Optional[object] = None
    created_product: bool = False


def match_and_link(
    *,
    supplier_offer,
    name: str,
    category: ProductCategory,
    barcode: Optional[str] = None,
    brand: Optional[str] = None,
    unit_quantity: Optional[int] = None,
    unit_measure: Optional[ProductUnit] = None,
) -> MatchOutcome:
    """Match one offer to the catalogue and act on the result.

    NEVER RAISES ON A MATCHING PROBLEM. This runs inside a supplier's
    import, and a matching failure must never fail their upload -- an
    unmatched offer is exactly how every offer behaved before the
    catalogue existed. The caller gets an outcome; the row is saved
    either way.
    """
    # THE KILL SWITCH IS CHECKED HERE, BEFORE ANYTHING IS PROPOSED, and
    # it has to be. Disabled matching used to reach propose_match, come
    # back with confidence 0.0, and be indistinguishable from "nothing
    # plausible found" -- so the gate said CREATE_NEW and switching
    # matching OFF filled the catalogue with a product per row. Caught by
    # a test; off now means off.
    if not matching_config.is_matching_enabled():
        return MatchOutcome(MatchDecision.SKIPPED, MatchTier.RULES, 0.0, None)

    # ALREADY MATCHED, NOTHING RELEVANT CHANGED -- do no work at all.
    #
    # This is the recurring-price-file case, which is the NORMAL case
    # rather than an optimisation for an edge one: the one-time import is
    # the exception, the weekly update IS the relationship. Prices and
    # stock move every week; names, barcodes, brands and pack sizes
    # almost never do.
    #
    # The offer keeps the product it already has. Nothing is re-proposed,
    # no review row is written, no trigram search runs.
    fingerprint = match_fingerprint(
        name=name,
        barcode=barcode,
        brand=brand,
        unit_quantity=unit_quantity,
        unit_measure=unit_measure,
    )
    if supplier_offer.product_id and supplier_offer.match_fingerprint == fingerprint:
        return MatchOutcome(
            MatchDecision.UNCHANGED, MatchTier.RULES, 0.0, supplier_offer.product_id
        )

    pack = PackSize(
        unit_quantity=unit_quantity,
        unit_measure=unit_measure.value if unit_measure else None,
    )

    proposal = matching_service.propose_match(
        name=name, barcode=barcode, brand=brand, pack=pack
    )
    decision = proposal.decision

    if decision is MatchDecision.AUTO_LINK and proposal.product_id:
        return _apply_link(supplier_offer, proposal, name, barcode, fingerprint)

    if decision is MatchDecision.REVIEW:
        MatchReviewRepository.record(
            supplier_offer_id=supplier_offer.id,
            source_text=name,
            proposed_product_id=proposal.product_id,
            tier=proposal.tier.value,
            confidence=proposal.confidence,
            reason=proposal.reason,
            status=ReviewStatus.PENDING,
            evidence=proposal.evidence,
        )
        # The offer stays UNMATCHED while it waits. That is deliberate:
        # applying a proposal nobody confirmed would defeat the point of
        # having a middle band at all.
        return MatchOutcome(decision, proposal.tier, proposal.confidence, None)

    # THE SIZE IT WAS MATCHED ON IS THE SIZE IT IS STORED WITH.
    #
    # This used to pass the caller's own unit_quantity/unit_measure
    # straight through -- which are None whenever a supplier gave a name
    # and no structured pack, which is most of the time. So a product
    # matched on "Ace Maize Meal 5kg", using a size read out of that
    # name, was CREATED with no size at all.
    #
    # Every such entry then became a magnet: _pack_agreement reads a
    # missing size as "unknown" rather than "different" -- correctly --
    # so the -0.40 penalty that exists for exactly this never fired
    # against it. The 2.5kg, the 5kg and the 25kg all collapsed into one
    # product, ten suppliers and R40.50 to R340.50 presented as a choice
    # between alternatives.
    effective = resolve_pack(pack, name)
    return _create_and_link(
        supplier_offer, proposal, name, category, brand,
        effective.unit_quantity, _as_product_unit(effective.unit_measure),
        barcode, fingerprint,
    )


def _as_product_unit(measure: Optional[str]) -> Optional[ProductUnit]:
    """A PackSize carries its measure as a plain string; the column
    wants the enum. An unrecognised value becomes None rather than
    raising -- a size we cannot express is the same as no size, and
    failing here would fail a supplier's upload over a unit."""
    if not measure:
        return None
    try:
        return ProductUnit(measure)
    except ValueError:
        return None


def _apply_link(
    supplier_offer, proposal: MatchProposal, name: str, barcode: Optional[str], fingerprint: str
) -> MatchOutcome:
    supplier_offer.product_id = proposal.product_id
    # STAMPED ONLY WHEN A PRODUCT IS ACTUALLY ATTACHED. A row that went
    # to review has no product yet, so it must be re-proposed next
    # import -- stamping it would mean a pending review silently became
    # permanent inaction.
    supplier_offer.match_fingerprint = fingerprint

    MatchReviewRepository.record(
        supplier_offer_id=supplier_offer.id,
        source_text=name,
        proposed_product_id=proposal.product_id,
        tier=proposal.tier.value,
        confidence=proposal.confidence,
        reason=proposal.reason,
        status=ReviewStatus.AUTO_APPLIED,
        evidence=proposal.evidence,
    )

    # AN ALIAS IS ONLY LEARNED FROM A BARCODE, never from fuzzy text.
    # Aliases are global -- one supplier's confirmed match answers the
    # same text for everyone afterwards -- so a wrong one is wrong for
    # the whole platform. A GTIN is the one automatic source certain
    # enough to earn that. Tier 3's guesses stay guesses.
    if proposal.tier is MatchTier.BARCODE and barcode:
        MatchAliasRepository.upsert(
            matching_key=normalise.matching_key(name),
            source_text=name,
            product_id=proposal.product_id,
            source=AliasSource.BARCODE,
        )

    return MatchOutcome(MatchDecision.AUTO_LINK, proposal.tier, proposal.confidence, proposal.product_id)


def _create_and_link(
    supplier_offer,
    proposal: MatchProposal,
    name: str,
    category: ProductCategory,
    brand: Optional[str],
    unit_quantity: Optional[int],
    unit_measure: Optional[ProductUnit],
    barcode: Optional[str],
    fingerprint: str,
) -> MatchOutcome:
    """Nothing plausible existed, so this product joins the catalogue.

    THE SUPPLIER'S OWN WORDS BECOME THE CATALOGUE NAME, unedited. It is
    the only name anyone has, and inventing a tidier one would make the
    entry harder for the next supplier to match against, not easier.
    """
    brand_row = None
    if brand:
        slug = normalise.brand_slug(brand)
        # resolve() first, so "COKE" attaches to the existing Coca-Cola
        # rather than creating a second brand under a shorthand.
        brand_row = BrandRepository.resolve(slug) or BrandRepository.get_or_create(brand, slug)

    product = CatalogueProductRepository.create(
        name=name,
        normalized_name=normalise.normalise_text(name),
        category=category,
        brand_id=brand_row.id if brand_row else None,
        unit_quantity=unit_quantity,
        unit_measure=unit_measure,
        # A barcode carried in only when it matched NOTHING -- otherwise
        # tier 0 would have found it. So it is safe to claim here, and
        # the unique constraint is the backstop if it is not.
        #
        # is_catalogue_usable, NOT just "is it truthy". THIS IS THE LINE
        # THAT WRITES A BARCODE INTO THE SHARED CATALOGUE, which makes
        # it the one place a bad one does permanent damage. Two ways it
        # could:
        #
        #   A RESTRICTED-CIRCULATION CODE (prefix 020-029, 040-049,
        #   200-299) is unique only inside one shop. Written here, the
        #   NEXT shop's completely different product carrying the same
        #   in-store number matches it at tier 0 with confidence 1.0.
        #   The unique constraint does not save us -- it is what makes
        #   the collision silent, because the second row never gets
        #   written and simply links to the first shop's product.
        #
        #   A FAILED CHECK DIGIT would claim a number that is not a
        #   GTIN at all, and reserve it against the real one.
        #
        # Dropping it costs this product nothing: it still exists, still
        # matches on text, and gains a barcode the day a supplier sends
        # a sound one.
        gtin=gtin.normalise_gtin(barcode) if gtin.is_catalogue_usable(barcode) else None,
    )

    supplier_offer.product_id = product.id
    supplier_offer.match_fingerprint = fingerprint

    MatchReviewRepository.record(
        supplier_offer_id=supplier_offer.id,
        source_text=name,
        proposed_product_id=product.id,
        tier=proposal.tier.value,
        confidence=proposal.confidence,
        reason="No existing product matched, so this one was added to the catalogue.",
        status=ReviewStatus.AUTO_APPLIED,
        # The evidence of what was CONSIDERED and rejected is the useful
        # part of a CREATE_NEW: "nothing matched" is only trustworthy if
        # you can see what was weighed. A row with no candidates at all
        # and a row whose best candidate scored 0.71 are very different
        # stories about the same outcome.
        evidence=proposal.evidence,
    )

    if barcode:
        MatchAliasRepository.upsert(
            matching_key=normalise.matching_key(name),
            source_text=name,
            product_id=product.id,
            source=AliasSource.BARCODE,
        )

    return MatchOutcome(
        MatchDecision.CREATE_NEW, proposal.tier, proposal.confidence, product.id, created_product=True
    )
