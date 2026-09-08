"""
Expanding the shorthand suppliers actually type.

MEASURED, NOT GUESSED. A two-supplier trial through the free tiers
resolved 40% of rows that should have matched. Reading the misses, none
of them were genuinely ambiguous -- they were abbreviations:

    W/STAR SUPER MAIZE 10KG      White Star
    SIMBA S&V CHIPS 125G         Salt & Vinegar
    5 ROSES TEA 100S             Five Roses
    SUNLIGHT DISHWASH LIQ 750ML  Dishwashing Liquid
    KOO BAKED BEANS TOM SAUCE    Tomato Sauce

That is a lookup table, not a language model. Every entry added here
removes rows from the paid tier permanently, and costs nothing to run
forever -- which makes this the cheapest accuracy in the whole system.

A WRONG EXPANSION IS WORSE THAN NONE, and that governs what belongs
here. Expanding "w" to "with" would make half the catalogue read alike;
expanding "van" to "vanilla" is right in a bakery aisle and wrong for a
delivery vehicle. The bar is: unambiguous in a South African FMCG
product name, or it does not go in. When unsure, leave it out -- an
unexpanded abbreviation costs one row going to a lower tier, while a
wrong one quietly merges two different products.

PHRASES BEFORE TOKENS, because the useful ones are multi-word. By the
time this runs, punctuation is already stripped, so "W/STAR" arrives as
"w star" and "S&V" as "s v" -- both meaningless as single tokens and
unambiguous as phrases. That is also why "s" and "v" are not in the
token map and never should be.

BOTH SIDES MUST BE EXPANDED. This runs inside normalise_text, so a
catalogue product's stored normalized_name and an incoming supplier row
are expanded identically. Expanding only the query would compare
"white star" against a stored "w star" and match nothing.

IF THE CATALOGUE EVER HAS ROWS WHEN THIS DICTIONARY CHANGES, they need
a backfill -- normalized_name is stored, so old rows keep the old
expansion. It was empty when this was written, so no backfill was
needed. A future change to these tables is a migration, not just an
edit.
"""
from __future__ import annotations

import re

from src.domains.catalogue.matching.algorithms.pack_size import MEASURE_ALIASES

#: Multi-word shorthand. Keys are what appears AFTER punctuation
#: stripping and lowercasing.
_PHRASES: dict[str, str] = {
    # Brand shorthand that survives punctuation stripping. These belong
    # here rather than in the brand alias table because they appear in
    # the product NAME, and a supplier who abbreviates the brand in the
    # name usually leaves the brand column empty too.
    "w star": "white star",
    "5 roses": "five roses",
    "sta soft": "stasoft",
    "bull brand": "bullbrand",
    # Flavour and variant shorthand.
    "s v": "salt vinegar",
    "s and v": "salt vinegar",
    "tom sauce": "tomato sauce",
    "chilli beef": "chilli beef",
    # Product-type shorthand.
    "dishwash liq": "dishwashing liquid",
    "washing pwdr": "washing powder",
    "washing pwd": "washing powder",
    "t paste": "toothpaste",
    "f cream": "full cream",
    "l fat": "low fat",
}

#: Single-token shorthand. Every one of these must be unambiguous in a
#: product name -- see the module docstring on why the bar is high.
_TOKENS: dict[str, str] = {
    "liq": "liquid",
    "pwdr": "powder",
    "pwd": "powder",
    "dishwash": "dishwashing",
    "orig": "original",
    "reg": "regular",
    "asstd": "assorted",
    "asst": "assorted",
    "choc": "chocolate",
    "marg": "margarine",
    "cond": "conditioner",
    "conc": "concentrate",
    "veg": "vegetable",
    "sunflwr": "sunflower",
    "btl": "bottle",
    "ctn": "carton",
    "sach": "sachet",
    "lrg": "large",
    "lge": "large",
    "sml": "small",
    "med": "medium",
    "dbl": "double",
    "mnt": "mint",
    "choco": "chocolate",
    "bisc": "biscuits",
    "crm": "cream",
    "swt": "sweet",
    "wht": "white",
    "brn": "brown",
}

#: Longest phrase first, so "washing pwdr" is not half-consumed by a
#: shorter key that happens to overlap.
_PHRASE_PATTERN = re.compile(
    r"\b(" + "|".join(sorted((re.escape(k) for k in _PHRASES), key=len, reverse=True)) + r")\b"
)


#: "2lt" and "2 litre" and "2l" are the same size written three ways,
#: and trigram similarity treats them as three different strings.
#: Rewriting them to one canonical form is the same class of fix as the
#: word abbreviations above and was found the same way -- by measuring:
#: SPRITE 2 LITRE, SUNFOIL OIL 2LT and CLOVER ... 1LT all failed to match
#: catalogue entries written with "2L" and "1L".
#:
#: The alias table is imported from pack_size rather than restated, so a
#: measure spelling added for parsing is automatically understood for
#: matching too.
_MEASURE_IN_TEXT = re.compile(
    r"(?<![a-z0-9])(\d+)\s*(" + "|".join(sorted(MEASURE_ALIASES, key=len, reverse=True)) + r")(?![a-z])"
)


def _canonical_measures(text: str) -> str:
    """"2 litre" and "2lt" both become "2l"; "750 ml" becomes "750ml"."""
    return _MEASURE_IN_TEXT.sub(
        lambda m: f"{m.group(1)}{MEASURE_ALIASES[m.group(2)].lower()}", text
    )


def expand(text: str) -> str:
    """Expand known shorthand in already-normalised text.

    Expects lowercase, punctuation-free, single-spaced input -- i.e.
    what normalise_text produces before this runs. Given anything else
    it simply matches less, never wrongly.
    """
    if not text:
        return ""

    expanded = _PHRASE_PATTERN.sub(lambda m: _PHRASES[m.group(1)], text)

    # Token pass. Words not in the map are left exactly as they are --
    # this never invents, only replaces what it recognises.
    expanded = " ".join(_TOKENS.get(word, word) for word in expanded.split(" ") if word)

    # Measures last, so "2 litre" has already survived the phrase and
    # token passes intact before being collapsed to "2l".
    return _canonical_measures(expanded)
