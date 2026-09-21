"""
Which of the feed's sections a shop can currently see, and why not.

A UI TOOL, NOT A FEATURE. Every builder in the business feed returns
None rather than an empty shell when it has nothing to show, which is
correct behaviour and makes designing the sections awkward: you cannot
style a rail you cannot make appear. This reports the state of all
twelve and can push a shop into the state that shows the missing ones.

    python scripts/feed_sections.py --email you@example.com
    python scripts/feed_sections.py --email you@example.com --seed-taps
    python scripts/feed_sections.py --email you@example.com --fresh-shop
    python scripts/feed_sections.py --email you@example.com --declared

TWO OF THE TWELVE CAN NEVER BOTH APPEAR, and it is worth knowing before
you go looking for the twelfth. "What stock do you buy?" shows only
while a shop has declared nothing; "Stock for your shop" shows only
once it has. They are two states of one question, so the ceiling is
ELEVEN visible at a time. --fresh-shop and --declared flip between them.

LOADS .env ITSELF, for the same reason run_tests.py does: the config
falls back to postgres:postgres, the real password lives in .env, and
it contains an '@' that reads as a host separator unless the DSN is
built properly. Without this the failure looks like a broken database.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()
os.environ.setdefault("MAIL_PROVIDER", "fake")

from src import create_app  # noqa: E402
from src.extensions import db  # noqa: E402

#: Every builder feed_service composes, in the order it composes them,
#: with what has to be true for it to return anything.
#:
#: KEPT BY HAND AND THAT IS THE COST OF THE TOOL. If a section is added
#: to _business_feed and not here, this prints eleven of twelve and
#: looks like the new one is broken. Cheaper than reflection that would
#: have to guess at each builder's own reason for silence.
SECTIONS = [
    ("categories", "Categories", "always"),
    ("tell-us-what-you-buy", "What stock do you buy?", "shop has declared NOTHING"),
    ("buy-it-again", "Buy it again", "3+ products ordered before"),
    ("left-off", "Pick up where you left off", "3+ products TAPPED and never ordered"),
    ("moving-fast", "Moving fast right now", "3+ products selling faster than usual"),
    ("stock-for-you", "Stock for your shop", "shop HAS declared categories"),
    ("your-suppliers", "Your suppliers", "1+ active connection"),
    ("sponsored", "Sponsored", "a visible supplier in the shop's categories"),
    ("invited-suppliers", "Joined through your invites", "3+ invitees verified"),
    ("not-ordered-yet", "Suppliers you haven't ordered from", "3+ never ordered from"),
    ("collect-near-you", "Collect near you", "3+ suppliers within range, shop collects"),
    ("explore-kinds", "Explore suppliers", "any supplier kind has stock"),
]


def _business(email: str):
    from src.domains.auth.models.user import User

    user = db.session.query(User).filter(User.email == email).one_or_none()
    if user is None:
        raise SystemExit(f"No account with email {email!r}")
    return user


def report(user) -> None:
    from src.domains.network.community.services import feed_service

    live = {section["id"] for section in feed_service.feed_for(user.id, "business")}

    print(f"\n{user.email}\n")
    print(f"{'':3} {'section':<36} {'':4} what it needs")
    print("-" * 92)
    for index, (section_id, title, needs) in enumerate(SECTIONS, start=1):
        mark = "OK " if section_id in live else "  -"
        print(f"{index:>2}. {title:<36} {mark}  {'' if section_id in live else needs}")
    print("-" * 92)
    print(f"{len(live)} of {len(SECTIONS)} showing (11 is the ceiling -- see the module docstring)\n")


def seed_taps(user, count: int = 4) -> int:
    """Make "Pick up where you left off" appear.

    TAPS ON PRODUCTS THE SHOP HAS NOT ORDERED, which is exactly what the
    rail is built from. Taken from the shop's OWN current feed rather
    than from any product in the database, because a tap on something
    the feed never showed them is not a state the app can reach and
    styling against impossible data teaches you nothing.
    """
    from src.domains.network.community.services import feed_service
    from src.domains.network.impressions.models.feed_impression import ImpressionItemType
    from src.domains.network.impressions.repositories.impression_repository import (
        ImpressionRepository,
        ImpressionRow,
    )
    from src.domains.network.orders.repositories.stock_order_repository import (
        StockOrderRepository,
    )

    ordered = {
        str(pid)
        for pid in StockOrderRepository.previously_ordered_product_ids_for_business(
            user.id, limit=200
        )
    }

    candidates = []
    for section in feed_service.feed_for(user.id, "business"):
        if section.get("type") != "PRODUCT_RAIL" or section["id"] == "buy-it-again":
            continue
        for position, product in enumerate(section["products"]):
            if product["id"] in ordered:
                continue
            candidates.append(
                ImpressionRow(
                    rail=section["id"],
                    position=position,
                    item_id=product["id"],
                    item_type=ImpressionItemType.PRODUCT,
                    supplier_profile_id=product.get("supplierId"),
                )
            )

    # ONE PER SUPPLIER FIRST, so the seeded rail is not four cards from
    # one wholesaler that the per-supplier cap then trims back to three
    # -- which would look like the seed failing rather than the cap
    # working.
    spread, seen = [], set()
    for row in candidates:
        if row.supplier_profile_id in seen:
            continue
        seen.add(row.supplier_profile_id)
        spread.append(row)
    chosen = (spread + [r for r in candidates if r not in spread])[:count]

    if not chosen:
        print("Nothing to tap -- every product in this feed has already been ordered.")
        return 0

    ImpressionRepository.bump(user.id, chosen, column="delivered", on=date.today())
    ImpressionRepository.bump(user.id, chosen, column="tapped", on=date.today())
    print(f"Tapped {len(chosen)} products across {len(seen)} suppliers.")
    return len(chosen)


def set_declared(user, *, declared: bool) -> None:
    """Flip between "What stock do you buy?" and "Stock for your shop".

    THE TWO ARE MUTUALLY EXCLUSIVE BY DESIGN -- the prompt disappears
    the moment it is answered -- so there is no arrangement of data that
    shows both, and a tool that let you try would be lying.
    """
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )
    from src.domains.catalogue.products.models.taxonomy import ProductCategory

    profile = BusinessProfileRepository.get_or_create_for_business(user.id)
    if declared:
        profile.buys_categories = [
            ProductCategory.BEVERAGES.value,
            ProductCategory.BAKERY.value,
        ]
        print("Declared 2 categories -- 'Stock for your shop' shows, the prompt hides.")
    else:
        # KEPT, NOT DELETED, so this is reversible with --declared. A
        # dev tool that loses the only copy of something is a dev tool
        # nobody runs twice.
        profile.buys_categories = []
        print("Cleared declarations -- the prompt shows, 'Stock for your shop' hides.")
    db.session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--seed-taps",
        action="store_true",
        help="tap unordered products so 'Pick up where you left off' appears",
    )
    parser.add_argument(
        "--fresh-shop", action="store_true", help="clear declarations (shows the prompt)"
    )
    parser.add_argument(
        "--declared", action="store_true", help="declare categories (shows stock-for-you)"
    )
    args = parser.parse_args()

    if args.fresh_shop and args.declared:
        raise SystemExit("--fresh-shop and --declared are opposites; pick one.")

    app = create_app("development")
    with app.app_context():
        user = _business(args.email)

        if args.fresh_shop:
            set_declared(user, declared=False)
        if args.declared:
            set_declared(user, declared=True)
        if args.seed_taps:
            seed_taps(user)

        report(user)


if __name__ == "__main__":
    main()
