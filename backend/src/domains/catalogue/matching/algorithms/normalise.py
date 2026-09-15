"""
Turning what a supplier typed into something comparable.

PURE FUNCTIONS, NO DATABASE, NO MODEL CALLS. Everything here is free,
instant, deterministic and unit-testable, which is the whole reason the
matching ladder starts here: tiers 0 to 3 must work with the AI switched
off forever, and this module is what makes tiers 1 and 2 possible at all.

THE TWO FORMS, AND WHY BOTH EXIST

  normalise_text("Coca-Cola  2LT")  -> "coca cola 2lt"
      Readable, spaces kept, punctuation gone. This is what gets stored
      as Product.normalized_name and what Postgres trigram similarity
      runs against, because trigrams need the word boundaries.

  matching_key("Coca-Cola 2LT")     -> "2ltcocacola"
      Tokens SORTED and joined with nothing. Word order and spacing stop
      mattering entirely, so "Coca-Cola 2LT" and "2LT COCA COLA" collapse
      to the same string. This is the tier-2 exact-match key.

Sorting the tokens is the point of the second form. Suppliers write the
same product in whatever order suits their own system, and a matcher
that treats "2L Coke" and "Coke 2L" as different things fails on the
easiest cases before it ever reaches a hard one.

ACCENTS ARE STRIPPED (café -> cafe) because a supplier's spreadsheet
encoding is not a fact about the product, and one exported from an older
system will disagree with one typed by hand.
"""
from __future__ import annotations

import re
import unicodedata

from src.domains.catalogue.matching.algorithms import abbreviations

#: A decimal separator BETWEEN TWO DIGITS, normalised to a full stop.
#: South African price and product files use both "1,5kg" and "1.5kg"
#: for the same size, and they have to reduce to one token.
_DECIMAL = re.compile(r"(?<=\d)[.,](?=\d)")

#: Anything that is not a letter, digit, full stop or space becomes a
#: space. Kept deliberately broad -- hyphens, slashes, brackets,
#: ampersands and asterisks all appear in real supplier files and none
#: of them carry meaning we can rely on.
#:
#: THE FULL STOP IS SPARED HERE AND REMOVED BELOW unless it is a
#: decimal point, which is the fix for a real and expensive collision:
#:
#:     "Ace Maize Meal 2.5kg" -> "ace maize meal 2 5kg"
#:                            -> tokens sorted and JOINED WITH NOTHING
#:                            -> "25kgacemaizemeal"
#:     "Ace Maize Meal 25kg"  -> "25kgacemaizemeal"
#:
#: Identical keys. Tier 2 links on an exact key match at confidence 1.0
#: with the words "matches this product word for word", and consults no
#: pack size at all -- so a 2.5kg bag and a 25kg bag became one product
#: with maximum confidence. Found by running the matcher over the
#: seeded catalogue: R40.50 next to R340.50, offered as alternatives.
_NON_ALNUM = re.compile(r"[^a-z0-9.\s]+")

#: A full stop that is NOT a decimal point -- end of a sentence, an
#: abbreviation, a stray. These still become spaces, exactly as before.
_STRAY_DOT = re.compile(r"(?<!\d)\.|\.(?!\d)")

_WHITESPACE = re.compile(r"\s+")


def strip_accents(value: str) -> str:
    """café -> cafe. NFKD splits a character into base plus combining
    mark, then the marks are dropped."""
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalise_text(value: str | None) -> str:
    """Lowercased, unaccented, punctuation-free, single-spaced, with
    known shorthand expanded.

    The readable form. Word order is PRESERVED, because this is what
    trigram similarity indexes and trigrams carry positional information
    that sorting would destroy.

    ABBREVIATION EXPANSION HAPPENS HERE, at the end, and that placement
    is the point: both a catalogue product's stored normalized_name and
    an incoming supplier row pass through this one function, so both
    sides are expanded identically. Expanding only the query would
    compare "white star" against a stored "w star" and match nothing.

    Punctuation is stripped BEFORE expansion, which is what turns
    "W/STAR" into "w star" and "S&V" into "s v" -- meaningless as single
    tokens, unambiguous as phrases. See abbreviations.py.
    """
    if not value:
        return ""
    text = strip_accents(value).lower()
    # DECIMALS FIRST, so "1,5kg" and "1.5kg" are one token before
    # anything else touches them -- and so the stray-dot pass below can
    # tell a decimal point from a full stop.
    text = _DECIMAL.sub(".", text)
    text = _NON_ALNUM.sub(" ", text)
    text = _STRAY_DOT.sub(" ", text)
    text = _WHITESPACE.sub(" ", text).strip()
    return abbreviations.expand(text)


def matching_key(value: str | None) -> str:
    """The tier-2 exact-match key: normalised, tokens sorted, joined.

    "Coca-Cola 2LT" and "2LT COCA COLA" both become "2ltcocacola", so a
    supplier who lists brand-first and one who lists size-first still
    land on the same product without anything cleverer running.

    DUPLICATE TOKENS ARE KEPT, not de-duplicated. "Bread bread rolls" is
    a different string from "bread rolls", and while the first is
    probably a typo, silently treating them as identical would be a
    guess -- and a guess made here is invisible, whereas one made at
    tier 3 or 4 arrives with a confidence score attached.

    THE TOKENS ARE JOINED WITH A SEPARATOR, and the one character is
    load-bearing. Joining with nothing makes the key AMBIGUOUS BY
    CONSTRUCTION: any two adjacent tokens concatenate into whatever a
    single token could have spelled. "bread" + "roll" collides with
    "breadroll", and -- the case that was actually found in the seeded
    catalogue -- "2" + "5kg" collided with "25kg".

    The decimal fix above stops that particular pair ever splitting, so
    this is belt and braces. It is kept because the class of collision
    is silent, arrives at tier 2 with confidence 1.0 and the words
    "matches word for word", and costs one character to make impossible.

    KEYS FROM BEFORE THIS CHANGE DO NOT MATCH KEYS AFTER IT. The stored
    matching_key on catalogue.match_aliases is the only place the old
    format lives; aliases are learned from barcodes and are re-learned
    on the next import that carries one, so the cost of invalidating
    them is one re-match rather than lost data.
    """
    normalised = normalise_text(value)
    if not normalised:
        return ""
    return "|".join(sorted(normalised.split(" ")))


def brand_slug(value: str | None) -> str:
    """The brand table's unique key. "Coca-Cola", "Coca Cola" and
    "COCA-COLA" all slug to "cocacola", which is what stops the same
    brand being created three times under three spellings."""
    return normalise_text(value).replace(" ", "")
