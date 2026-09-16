"""
Reading a brand out of the way suppliers actually write a product name.

WHY THIS EXISTS, measured on the seeded catalogue before it did:

    Fanta Orange Cooldrink 500ml  ->  proposed: Coca-Cola Cooldrink 500ml
    Sunfoil Cooking Oil 2L        ->  proposed: D'lite Cooking Oil 2L
    aQuelle Still Water 5L        ->  proposed: Bonaqua Still Water 5L
    Maq Washing Powder 3kg        ->  proposed: Omo Washing Powder 3kg

Competitors, proposed as the same product. 47 of the 72 distinct
decisions waiting in the review queue were this, and every one of them
was wrong.

THE CAUSE WAS NOT THE SCORER. confidence.score_rules_match already
penalises a brand disagreement by -0.30, which would have taken
Fanta-against-Coca-Cola from 75% to 45% and out of contention
entirely. The penalty never fired, because `brand` is not a column on
supplier_offers and nothing derived it from the name -- so
_brand_agreement saw None on one side, correctly returned "unknown",
and the tier fell through to text similarity alone.

This is the same shape as the three pack-size bugs before it: the fact
is sitting in the name, the code that could read it is never asked.

A LIST, NOT A GUESSER, AND THAT IS THE DESIGN. The tempting version
infers the brand from the first word or two. It fails immediately on
real data -- these are all leading words in this catalogue:

    Generic (41 products)   White Bread     Potatoes 10kg
    Washing Powder          Maize Meal      Pack of 6

and it fails the other way on multi-word brands, where "White Star"
would be read as "White" and collide with "White Bread". Guessing
wrong here is worse than not guessing: a WRONG brand makes
_brand_agreement return False against the correct product and
suppresses a match that should have happened.

So brands are declared. The list below is drawn from what is actually
in this catalogue plus the common South African FMCG names around
them; anything not on it returns None, which leaves the tier exactly
where it was before this module existed. Adding a brand is one line,
and it is the cheapest possible way to retire a class of bad match.

LONGEST MATCH WINS, ON WORD BOUNDARIES. "White Star Maize Meal 5kg"
matches "White Star" and not "White"; "Ace Maize Meal" matches "Ace"
while "Acetone Remover" matches nothing, because the comparison is
over whole words rather than characters.
"""
from __future__ import annotations

from typing import Optional

from src.domains.catalogue.matching.algorithms import normalise

#: Brands this catalogue knows, as they should be SHOWN to a human.
#:
#: DRAWN FROM REAL DATA. Every name here leads at least one product in
#: the seeded catalogue, or is a household South African FMCG brand
#: sitting beside one. This is reference data, not a guess at the
#: market -- a brand nobody stocks costs a wasted comparison, and a
#: brand that is missing costs nothing at all beyond the status quo.
#:
#: MULTI-WORD ENTRIES ARE THE POINT. Half the failures a first-word
#: heuristic produces are here: White Star, Super Sun, Aunt Caroline,
#: Liqui Fruit, Sea Harvest, Yum Yum.
KNOWN_BRANDS: tuple[str, ...] = (
    # Multi-word first for readability; the matcher sorts by length
    # itself and does not rely on this order.
    "White Star",
    "Super Sun",
    "Aunt Caroline",
    "Liqui Fruit",
    "Sea Harvest",
    "Yum Yum",
    "Golden Cloud",
    "Five Roses",
    "All Gold",
    "I&J",
    # Staples and grains
    "Ace",
    "Iwisa",
    "Imbo",
    "Tastic",
    "Spekko",
    "Nyala",
    "Excella",
    "Selati",
    "Huletts",
    "Snowflake",
    "Cerebos",
    "Marina",
    "Sunfoil",
    "D'lite",
    "Koo",
    "Rhodes",
    # Bakery
    "Albany",
    "Sasko",
    "Blue Ribbon",
    "Bakers",
    "Romany",
    "Eet-Sum-Mor",
    "Beacon",
    "Manhattan",
    "Wilson's",
    # Dairy, eggs, chilled
    "Clover",
    "Parmalat",
    "Everfresh",
    "Nulaid",
    "Rama",
    "Stork",
    "Dairymaid",
    # Drinks
    "Coca-Cola",
    "Fanta",
    "Sprite",
    "Stoney",
    "Score",
    "Play",
    # Seen in the review queue as an unrecognised brand: "Dragon Energy
    # Drink 440ml x12" was being proposed against Play and Score, and
    # nothing could object because Dragon was not declared.
    "Dragon",
    "Monster",
    "Red Bull",
    "Valpre",
    "aQuelle",
    "Bonaqua",
    "Nestle",
    "Nescafe",
    "Ricoffy",
    "Joko",
    "Five Star",
    # Snacks
    "Simba",
    "Lay's",
    "Doritos",
    "Nestum",
    "Purity",
    # Cleaning and laundry
    "Omo",
    "Surf",
    "Maq",
    "Sunlight",
    "Jik",
    "Handy Andy",
    "Domestos",
    "Vim",
    # Personal care
    "Colgate",
    "Aquafresh",
    "Sensodyne",
    "Protex",
    "Lifebuoy",
    "Lux",
    "Dove",
    "Vaseline",
    "Nivea",
    "Shield",
    "Sunsilk",
    "Pantene",
    "Johnson's",
    "Sofn'free",
    "S-Curl",
    "Twinsaver",
    "Baby Soft",
    "Pampers",
    "Huggies",
    # Cooking and pantry
    "Knorr",
    "Royco",
    "Robertsons",
    "Aromat",
    "Black Cat",
    # Frozen and protein
    "Rainbow",
    "Renown",
    "Enterprise",
    # Stationery and general
    "BIC",
    "Duracell",
    "Eveready",
    "Pilot",
    "Staedtler",
    "Lion",
    "Orbit",
)


def _words(value: str) -> list[str]:
    """Normalised words, using the SAME normaliser the matcher uses.

    IMPORTANT THAT IT IS THE SAME ONE: normalise_text expands
    abbreviations, so "W/STAR Maize" becomes "white star maize" before
    this ever sees it, and the multi-word entry above matches a
    shorthand nobody listed.
    """
    return normalise.normalise_text(value).split(" ") if value else []


#: Brand words, longest first, so "White Star" is tried before "White"
#: would be if it were ever added.
_INDEXED: list[tuple[list[str], str]] = sorted(
    ((_words(brand), brand) for brand in KNOWN_BRANDS),
    key=lambda pair: len(pair[0]),
    reverse=True,
)


def detect_brand(name: Optional[str]) -> Optional[str]:
    """The brand in this product name, or None.

    ANYWHERE IN THE NAME, NOT ONLY AT THE START. Suppliers write
    "2L COCA COLA" as often as "Coca-Cola 2L", and the matching key
    already treats word order as meaningless -- a brand reader that
    insisted on position would disagree with the tier that uses it.

    NONE IS A SAFE ANSWER AND A WRONG ONE IS NOT. An unrecognised brand
    leaves _brand_agreement returning "unknown", which is exactly the
    behaviour before this module existed. A wrong brand would make it
    return False against the RIGHT product and suppress a good match --
    so this only ever answers from the declared list.
    """
    haystack = _words(name)
    if not haystack:
        return None

    for brand_words, display in _INDEXED:
        if not brand_words:
            continue
        span = len(brand_words)
        for start in range(len(haystack) - span + 1):
            if haystack[start : start + span] == brand_words:
                return display
    return None


def resolve_brand(brand: Optional[str], name: Optional[str]) -> Optional[str]:
    """The brand to actually USE: what the caller supplied, or what the
    description says.

    ONE RULE, ONE PLACE, for the same reason resolve_pack exists. The
    proposal tier and the create-a-product path both need this fallback,
    and when the equivalent for pack size was written in only one of
    them the result was a catalogue full of products missing the very
    fact they had been matched on.

    THE CALLER STILL WINS. A brand that arrived with an import is
    something a supplier stated; one read out of a name is something we
    inferred, and the stated fact outranks the inference.
    """
    if brand and brand.strip():
        return brand
    return detect_brand(name)
