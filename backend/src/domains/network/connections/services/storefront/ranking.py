"""
How products are ORDERED inside the brand profile's category strips.

PURE BY DESIGN -- every function here takes plain dicts (the
product_dto shape) plus whatever precomputed lookup a signal needs, and
returns a sort key. Nothing in this module imports Flask, SQLAlchemy, a
repository or a model, and nothing here performs a query. That is the
whole point: a ranking change is a pure-function change, testable in
milliseconds, and a new signal that needs data (order counts,
repurchase history) is fetched by showcase_service and PASSED IN rather
than reached for from here.
"""
from __future__ import annotations


def _discount_fraction(d: dict) -> float:
    """How deep this product's discount is, 0.0 when there isn't one.
    A compare-at price at or below the selling price is not a discount
    -- it's stale or mis-entered data, and must never rank a product
    UP; treated as no discount at all rather than a negative."""
    compare_at = d.get("compareAtPriceCents")
    price = d.get("priceCents") or 0
    if not compare_at or compare_at <= price:
        return 0.0
    return (compare_at - price) / compare_at


def showcase_sort_key(d: dict, pinned_ids: set):
    """The showcase's ranking, in priority order. Every signal here is
    one the SUPPLIER already owns -- stock, price, discount, recency.
    Deliberately nothing derived from how businesses browse: no view
    counts, no per-viewer personalisation, no cross-business
    behavioural data. That was a conscious product decision, not an
    oversight -- it keeps this endpoint free of any new data collection
    about who looked at what, consistent with the privacy framing in
    _common.py's own docstring (the same reasoning that had
    phone/email search removed rather than merely masked).

    Order of precedence:
      1. PINNED -- the supplier's own explicit "feature this" wins over
         every computed signal. Optional: a supplier who never pins
         anything simply gets the ranking below, which is why pinning
         costs them nothing.
      2. IN STOCK -- an out-of-stock product in a shopfront strip is a
         dead end; it still appears (honestly badged), just never above
         something orderable.
      3. DEEPEST DISCOUNT -- the strongest genuine "look at this" signal
         a supplier gives without doing any extra work; it comes free
         from a compare-at price they already set.
      4. NEWEST -- falls out of the caller's own ordering
         (ProductRepository.list_for_supplier sorts created_at DESC) via
         Python's stable sort, so it needs no key of its own and no
         timestamp added to the product dict.
    """
    return (
        d["id"] not in pinned_ids,  # False (pinned) sorts before True
        not d.get("inStock", False),
        -_discount_fraction(d),
    )
