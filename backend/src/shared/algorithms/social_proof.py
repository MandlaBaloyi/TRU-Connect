"""
"27 businesses bought this."

THE ONLY CLAIM ON A PRODUCT CARD THAT IS NOBODY'S OPINION. The price is
the supplier's. The ranking is ours. This is what other shops actually
did, and it is the one line a competitor without real trade cannot put
on a screen -- which makes it worth more than anything the engine
infers.

IT COUNTS BUSINESSES, NOT UNITS. A units count lets one wholesale buyer
manufacture a bestseller by ordering forty cases. A count of distinct
businesses cannot be moved by anybody except more businesses, which is
exactly the property that makes the number trustworthy.

NO MINIMUM -- MANDLA'S CALL, and the reasoning is worth recording
because I argued the other way first.

  I proposed a floor of five, on the same k-anonymity grounds
  gap_service uses (MIN_SHOPS_TO_REPORT): an aggregate of one is a
  sentence about a person.

  THAT ARGUMENT DOES NOT TRANSFER, and this is why. The gap report
  pairs a count with a CATEGORY and eventually an AREA -- "1 shop in
  Diepsloot needs airtime" narrows to a person, and it is read by
  suppliers, who can act on it. This number carries no location, no
  category targeting and no supplier audience: it says one of the
  platform's businesses bought this product, to another business, with
  nothing to narrow it by. The reader learns that somebody did, not who.

  AND THE PRODUCT COST OF A FLOOR IS REAL. A new catalogue is made
  almost entirely of products nobody has bought five times yet, so a
  floor would blank the badge precisely where the first proof of life
  matters most -- the early days, when one real purchase is the most
  encouraging thing on the screen.

  WHAT WOULD CHANGE IT: this number ever becoming visible to suppliers,
  or ever being shown alongside a location or a named buyer. Either of
  those puts the gap_service argument back in force.

IT LIVES IN shared/ BECAUSE TWO DOMAINS RENDER IT. The catalogue
browse and the community feed both build product cards, and the
architecture test refused the first version of this file outright:
nothing may import the community feed (test_community_is_a_composer),
so a rule both surfaces need cannot live inside it. It depends on no
domain -- an integer in, a sentence out -- which is exactly the test
shared/ applies.

NEVER "A FEW", NEVER ROUNDED. The number is exact or it is absent.
Rounding invents a claim nobody can check, and "a few" is the kind of
soft language V2_15 Part 12 bans as a dark pattern -- everything the
feed says must be true.
"""
from __future__ import annotations

from typing import Optional

#: Below this the badge is hidden. ZERO means "only hide it when nobody
#: has bought it", which is not a privacy floor at all -- it is the
#: absence of one, kept as a named constant so the decision above stays
#: visible and reversible in ONE place rather than being an `if count:`
#: buried in a card builder.
MIN_BUYERS_TO_SHOW = 0


def should_show(buyer_count: Optional[int]) -> bool:
    """Is there a real number to put on the card?

    A product nobody has bought yet gets NO BADGE rather than "0
    businesses bought this" -- which is true, useless, and reads as a
    warning. Silence is right here precisely because the badge is a
    positive claim: its absence says nothing, while a zero says
    something discouraging that we did not mean.
    """
    return bool(buyer_count) and buyer_count > MIN_BUYERS_TO_SHOW


def label(buyer_count: Optional[int]) -> Optional[str]:
    """The sentence, or None when there is nothing to say.

    BUILT HERE RATHER THAN IN THE APP so the wording is one decision.
    Two clients already render the same card shape (the feed and the
    catalogue browse), and a phrase duplicated across them is a phrase
    that will disagree with itself within a release.
    """
    if not should_show(buyer_count):
        return None
    if buyer_count == 1:
        return "1 business bought this"
    return f"{buyer_count:,} businesses bought this"
