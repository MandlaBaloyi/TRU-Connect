"""
Browsing the catalogue across every supplier.

THE QUERY THAT DID NOT EXIST. Every product read in this codebase is
scoped to ONE supplier's shopfront -- catalog_service,
list_profile_products, previously_ordered_product_ids. Nothing could
answer "what drinks can I buy, from anyone", which is why tapping a
category chip routed to SUPPLIER search and found shops instead of
stock.

IT BROWSES OFFERS, GROUPED BY CATALOGUE PRODUCT -- NOT THE CATALOGUE.
That is a deliberate inversion of what docs/v2/V2_15 Book Two proposed,
and the data is the reason: on 2026-09-14 there were 28 supplier offers,
ZERO of them matched, and ZERO catalogue products. A catalogue-first
browse would have returned an empty screen and looked like a bug.

So the catalogue is what makes the result BETTER, never what makes it
POSSIBLE:

    matching worked   three suppliers' "WHT SUGR 2.5KG", "White Sugar
                      2.5kg" and "Sugar White 2.5KG" collapse to ONE
                      card, and the shop picks a supplier rather than
                      squinting at three spellings
    matching has not  each offer stands alone. Honest, and exactly what
                      a shop would see on a shelf anyway

As match coverage rises the same screen quietly improves, with no
change here. That is the property worth having.

THE CURTAIN APPLIES, in SQL rather than afterwards -- a LIMIT in front
of an in-Python filter returns fewer rows than asked for, which is the
hazard visibility.py's own docstring warns about.

NARROWING IS THE WHOLE JOB OF THIS FILE NOW. Seventeen flat categories
mean "Food & Grocery" is one bucket holding flour, oil, sugar and rice,
and no card design makes a thousand of those scannable -- nobody browses
a thousand products, they arrive wanting cooking oil. So search, brand
and "my suppliers" are not decoration on a list: they are the list's
reason for being usable at all.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from src.extensions import db

#: How many offers to pull per requested card.
#:
#: GROUPING HAPPENS AFTER THE QUERY, so asking the database for exactly
#: `limit` offers would return fewer than `limit` CARDS whenever any two
#: of them are the same product. Four is generous for a market where a
#: product is carried by a handful of suppliers, and it is bounded --
#: never "fetch everything and sort in Python".
_OVERFETCH = 4

#: THE SORTS THE DATABASE CAN DO CHEAPLY, and deliberately no more.
#:
#: "Most bought" is the sort a shopkeeper would most like, and its
#: absence is a decision rather than an omission: it needs an aggregate
#: over stock_order_items for the WHOLE filtered catalogue on every
#: browse. That is exactly the query-cost-per-open problem the feed
#: already carries, so it belongs behind the cache with the market-wide
#: rails, not in a query a shopper triggers by tapping a chip.
SORTS = ("name", "price_asc", "price_desc")


def _filtered(
    *,
    category: Optional[str] = None,
    categories: Optional[List[str]] = None,
    search: Optional[str] = None,
    kind: Optional[str] = None,
    supplier_ids: Optional[List] = None,
):
    """The query every read in this file starts from.

    ONE BUILDER FOR THE PAGE, THE COUNT AND THE FACETS, because they
    have to agree. A header reading "253 products" above a list built
    from a different filter chain is worse than no header at all, and
    three copies of a chain drift the first time one of them gains a
    clause.
    """
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer
    from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierProfile
    from src.domains.verification.visibility import visible_filter

    query = (
        db.session.query(SupplierOffer)
        .join(SupplierProfile, SupplierProfile.id == SupplierOffer.supplier_profile_id)
        .filter(
            visible_filter(),
            SupplierOffer.is_deleted.is_(False),
            SupplierOffer.is_archived.is_(False),
        )
    )

    # SEVERAL CATEGORIES IN ONE QUERY, because the demand engine asks
    # for everything a shop buys at once. Looping a single-category
    # browse would be one query per declared category -- the N+1 this
    # codebase has removed three times now, arriving by a new route.
    if categories:
        query = query.filter(SupplierOffer.category.in_(categories))
    elif category:
        query = query.filter(SupplierOffer.category == category)

    if search:
        # ILIKE with the wildcards escaped -- a shopper typing "50%"
        # should search for "50%", not match everything. Same treatment
        # as the supplier search (test_like_escaping.py exists because
        # this was got wrong once already).
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.filter(SupplierOffer.name.ilike(f"%{escaped}%", escape="\\"))

    if kind:
        # WHAT SORT OF BUSINESS IS SELLING IT. Stated by the supplier,
        # never inferred -- SupplierKind's own docstring makes the case:
        # "Seshego Cash & Carry" is a wholesaler whose name says
        # nothing, and "Wholesale Beauty Supplies" is a retailer whose
        # name says the opposite.
        query = query.filter(SupplierProfile.supplier_kind == kind)

    if supplier_ids is not None:
        # AN EMPTY LIST MEANS NOTHING MATCHES, and that is the honest
        # answer rather than "no filter applied". A shop with no
        # connections asking for "my suppliers only" has asked for the
        # empty set, and showing them the whole market instead would be
        # the screen ignoring the control they just used.
        query = query.filter(SupplierOffer.supplier_profile_id.in_(supplier_ids))

    return query


def _card_key():
    """The expression that counts CARDS rather than offers.

    THIS IS _group_by_product's KEY, WRITTEN IN SQL. That function keys
    a group on `offer.product_id or ("offer", offer.id)` -- matched
    offers collapse onto their catalogue product, an unmatched offer
    stands alone. COALESCE over the two columns is the same rule, so
    the count and the grouping cannot disagree about what a card is.

    WHY IT IS WORTH THE COALESCE. Counting offers was the first version
    and it produced a number that was true and useless: a brand chip
    read "Iwisa 16" and opened onto three cards, because sixteen
    offers of Iwisa from six wholesalers are three products -- Maize
    Meal in 2.5kg, 5kg and 25kg. Labelling it "offers" made the number
    accurate without making it mean anything, which is the worse
    failure: a reader does not want a vocabulary lesson, they want to
    know how many things they are about to look at.
    """
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer

    return db.func.coalesce(
        db.cast(SupplierOffer.product_id, db.String),
        db.cast(SupplierOffer.id, db.String),
    )


def count(
    *,
    category: Optional[str] = None,
    categories: Optional[List[str]] = None,
    search: Optional[str] = None,
    kind: Optional[str] = None,
    supplier_ids: Optional[List] = None,
) -> int:
    """How many CARDS match -- the number the screen actually shows.

    NOT AN OFFER COUNT. See _card_key: three suppliers carrying the same
    sugar are three offers and ONE card, and a header promising three
    is a header that lies the moment anybody scrolls.
    """
    return (
        _filtered(
            category=category,
            categories=categories,
            search=search,
            kind=kind,
            supplier_ids=supplier_ids,
        )
        .with_entities(db.func.count(db.distinct(_card_key())))
        .scalar()
        or 0
    )


def kinds_in(
    *,
    category: Optional[str] = None,
    categories: Optional[List[str]] = None,
    search: Optional[str] = None,
    supplier_ids: Optional[List] = None,
) -> List[dict]:
    """Which SORTS of supplier have stock in this result.

    THIS REPLACED BRAND CHIPS, and the reason is worth keeping. Brand
    was the first axis tried, on the argument that a shopkeeper asks
    for Huletts rather than for "sweeteners". True, and the chips were
    still wrong: a category of any size has dozens of brands, White
    Star alone carries a shelf of flours, and a row of twenty brand
    chips is a second scrolling problem sitting on top of the first.
    Searching "Huletts" answers the brand question better than any
    finite row of chips could, and the search box is right there.

    WHAT A ROW OF CHIPS IS ACTUALLY GOOD AT is a small, closed set
    where every option is a different KIND of answer. Supplier kind is
    exactly that -- four values, stated by the supplier, and each one
    changes what an order looks like: a manufacturer is a different
    proposition from a cash-and-carry.

    IT ALSO MATCHES EXPLORE. The same four words, the same glyphs, the
    same vocabulary on both screens. Two rows of chips that narrow the
    market should not teach two different languages.

    COUNTS ARE CARDS, like every number on this screen.
    """
    from src.domains.supplier.supplier_profile.models.supplier_profile import (
        SupplierKind,
        SupplierProfile,
    )

    rows = (
        _filtered(
            category=category,
            categories=categories,
            search=search,
            supplier_ids=supplier_ids,
        )
        .with_entities(
            SupplierProfile.supplier_kind,
            db.func.count(db.distinct(_card_key())).label("n"),
        )
        .group_by(SupplierProfile.supplier_kind)
        .all()
    )

    found = {
        getattr(k, "value", k): int(n)
        for k, n in rows
        # UNSPECIFIED IS NOT A FILTER. It is the honest default for a
        # supplier who has not said, and "browse the ones who did not
        # tell us what they are" is not a thing anybody wants to tap --
        # the same rule explore_service.kinds_with_suppliers follows.
        if getattr(k, "value", k) != SupplierKind.UNSPECIFIED.value
    }

    # A STABLE ORDER, from the enum rather than from whatever the
    # database returned, so the chips do not move between visits.
    return [
        {"id": k.value, "name": k.value, "count": found[k.value]}
        for k in SupplierKind
        if k.value in found
    ]


def suppliers_in(
    *,
    category: Optional[str] = None,
    categories: Optional[List[str]] = None,
    search: Optional[str] = None,
    supplier_ids: Optional[List] = None,
    limit: int = 12,
) -> List[dict]:
    """Which suppliers actually carry stock in this result.

    THE SECOND AXIS, AND THE RIGHT ONE ONCE "MY SUPPLIERS" IS ON. A
    shop that has narrowed to its own four wholesalers is no longer
    asking "which brand" -- it is asking "which of my four has this",
    because that decides whether an order is one delivery or three.

    IT ALSO FIXES A DISAPPEARING ROW. Brand facets come through the
    catalogue product, so a shop whose suppliers carry mostly unmatched
    stock saw the brand chips vanish the moment it tapped My suppliers
    -- the control removed the controls next to it, which reads as the
    screen breaking rather than as a filter working.

    COUNTS ARE CARDS, like every other number on this screen, so a chip
    saying 4 opens onto four products.
    """
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer
    from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierProfile

    rows = (
        _filtered(
            category=category,
            categories=categories,
            search=search,
            supplier_ids=supplier_ids,
        )
        .with_entities(
            SupplierProfile.id,
            SupplierProfile.business_name,
            db.func.count(db.distinct(_card_key())).label("n"),
        )
        .group_by(SupplierProfile.id, SupplierProfile.business_name)
        .order_by(db.desc("n"), SupplierProfile.business_name.asc())
        .limit(limit)
        .all()
    )
    return [{"id": str(sid), "name": name, "count": int(n)} for sid, name, n in rows]


def browse(
    *,
    category: Optional[str] = None,
    categories: Optional[List[str]] = None,
    search: Optional[str] = None,
    kind: Optional[str] = None,
    supplier_ids: Optional[List] = None,
    sort: str = "name",
    limit: int = 24,
    offset: int = 0,
) -> List[List]:
    """Live offers from visible suppliers, grouped into one list per
    catalogue product.

    Returns a list of GROUPS, each a list of SupplierOffer rows for the
    same product, so the caller decides which to show (offer_selection)
    rather than this deciding for them. A repository that picked would
    be making a product decision in a place nobody looks for one.

    ───────────────────────────────────────────────────────────────────
    TWO QUERIES, AND OFFSET COUNTS CARDS. This is the fix for a bug that
    only became visible once the screen could scroll.

    The first version over-fetched OFFERS -- limit x _OVERFETCH of them
    -- and grouped in Python. That returns roughly `limit` cards, which
    is fine for one page and wrong for two: the caller advances offset
    by the CARDS it received, while the query applies it to OFFER ROWS.
    Page one read ninety-six offers and returned twenty-four cards; page
    two asked for offset twenty-four and re-read offers 24-120, so
    products already on screen came back again. React reported it as
    "encountered two children with the same key", which is the symptom
    of a paging bug rather than a rendering one -- and further down the
    list the same arithmetic silently SKIPS products, which nothing
    reports at all.

    So the page is chosen over card keys:

        1. GROUP BY the card key, order, LIMIT/OFFSET -- an exact page
           of products, because the thing being counted is the thing
           being shown.
        2. Fetch every offer belonging to those keys, so
           offer_selection still sees the whole group and can pick on
           stock and incumbency.

    TWO BOUNDED QUERIES BEAT ONE UNBOUNDED GUESS. _OVERFETCH was always
    an estimate of how many offers make `limit` cards; when it guessed
    low a page came back short, and when it guessed high it read rows
    for nothing. Neither failure is possible now.
    """
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer

    key = _card_key()

    # STEP 1 -- THE PAGE OF CARDS. Aggregates rather than raw columns,
    # because after GROUP BY there is no single name or price: a product
    # carried by six wholesalers has six of each. MIN(name) is stable
    # (they are the same product), and the price aggregate follows the
    # direction being sorted so "cheapest first" means the cheapest
    # OFFER of each product, which is what a shopper is comparing.
    page = _filtered(
        category=category,
        categories=categories,
        search=search,
        kind=kind,
        supplier_ids=supplier_ids,
    ).with_entities(key.label("card_key"))

    if sort == "price_asc":
        page = page.group_by(key).order_by(
            db.func.min(SupplierOffer.price_cents).asc(), db.func.min(SupplierOffer.name).asc()
        )
    elif sort == "price_desc":
        page = page.group_by(key).order_by(
            db.func.max(SupplierOffer.price_cents).desc(), db.func.min(SupplierOffer.name).asc()
        )
    else:
        page = page.group_by(key).order_by(db.func.min(SupplierOffer.name).asc())

    card_keys = [row[0] for row in page.offset(offset).limit(limit).all()]
    if not card_keys:
        return []

    # STEP 2 -- EVERY OFFER FOR THOSE CARDS. The filters are applied
    # again rather than trusted from step one: "my suppliers" and the
    # brand filter must narrow WHICH offers a card is built from, not
    # only which cards appear. Without it, filtering to one wholesaler
    # would still show a card priced from a different one.
    offers = (
        _filtered(
            category=category,
            categories=categories,
            search=search,
            kind=kind,
            supplier_ids=supplier_ids,
        )
        .filter(key.in_(card_keys))
        .all()
    )

    # THE ORDER COMES FROM STEP ONE, NOT FROM STEP TWO. The second query
    # has no ORDER BY worth having -- it is an IN over a set -- so the
    # page's order is re-imposed here from the keys the database already
    # sorted.
    by_key: dict = {}
    for offer in offers:
        by_key.setdefault(str(offer.product_id or offer.id), []).append(offer)

    return [by_key[card_key] for card_key in card_keys if card_key in by_key]


def _group_by_product(offers: List, limit: int) -> List[List]:
    """One group per catalogue product; an UNMATCHED offer is its own
    group.

    STILL HERE BECAUSE IT IS THE DEFINITION. browse() now groups in SQL
    (_card_key is this function's key expressed there), and this remains
    as the readable statement of the rule plus the path any caller
    holding offers in memory can use. If the two ever disagree, this one
    is right and the SQL is wrong.

    KEYED ON THE OFFER'S OWN ID WHEN product_id IS NULL, never on the
    name. Two suppliers spelling the same thing differently are not
    known to be the same thing -- that is precisely the judgement the
    matching ladder makes with a confidence score and a review queue,
    and guessing it here with a string comparison would be that whole
    system done badly in one line.
    """
    groups: dict = {}
    order: List = []

    for offer in offers:
        key = offer.product_id or ("offer", offer.id)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(offer)

    return [groups[key] for key in order[:limit]]


def count_for_category(category: str) -> int:
    """How many live offers a category actually has.

    Used to decide whether a chip is worth showing at all: a category
    chip that leads to an empty screen is worse than one that is absent,
    and it is the first thing a new user taps.
    """
    return count(category=category)
