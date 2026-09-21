"""
What the feed has counted so far.

A DEV TOOL, NOT A FEATURE. Impressions are deliberately invisible in the
app -- there is no screen for them and there should not be -- so the
only way to watch the table fill while testing on a phone is to look at
it directly. This is that look, and nothing in src/ imports it.

    python scripts/show_impressions.py                 everything
    python scripts/show_impressions.py --email a@b.co   one shop
    python scripts/show_impressions.py --watch          refresh every 3s

WHY A SCRIPT RATHER THAN A flask COMMAND. src/cli/ is for work that has
no screen yet but is real staff work -- approving a supplier, resolving
a catalogue review. This is somebody checking whether a counter moved
while they hold a phone, which is the same shape as run_tests.py: dev
plumbing that lives in scripts/ and loads .env itself.

LOADS .env BEFORE THE APP FACTORY, for the reason run_tests.py exists at
all: TestingConfig and DevelopmentConfig both fall back to
postgres:postgres, the real password lives in .env, and it contains an
'@' that reads as the host separator unless the DSN is built properly.
Without this line the failure looks like a broken database rather than a
missing dotenv call.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()
os.environ.setdefault("MAIL_PROVIDER", "fake")

from src import create_app  # noqa: E402
from src.extensions import db  # noqa: E402


def rows(email: str | None):
    from src.domains.auth.models.user import User
    from src.domains.network.impressions.models.feed_impression import FeedImpression

    query = db.session.query(FeedImpression, User.email).join(
        User, User.id == FeedImpression.business_id
    )
    if email:
        query = query.filter(User.email == email)
    return query.order_by(
        FeedImpression.day.desc(),
        User.email,
        FeedImpression.rail,
        FeedImpression.position,
    ).all()


def show(email: str | None) -> None:
    found = rows(email)
    if not found:
        print("No impressions yet. Open the Community tab as a business.")
        return

    print(f"{'shop':<26} {'rail':<20} {'pos':>3} {'type':<9} {'deliv':>5} {'tap':>4}")
    print("-" * 74)

    delivered = tapped = 0
    for impression, shop in found:
        delivered += impression.delivered
        tapped += impression.tapped
        print(
            f"{shop[:25]:<26} {impression.rail[:19]:<20} {impression.position:>3} "
            f"{impression.item_type.value:<9} {impression.delivered:>5} "
            f"{impression.tapped:>4}"
        )

    # THE THREE NUMBERS THAT MATTER WHILE TESTING. Rows should stay flat
    # while delivered climbs -- if the row count rises every time the tab
    # is opened, the upsert has become an insert and the whole grain
    # decision is gone. That is the failure this script exists to make
    # obvious.
    print("-" * 74)
    rate = f"{(tapped / delivered * 100):.1f}%" if delivered else "n/a"
    print(f"{len(found)} rows · {delivered} delivered · {tapped} tapped · tap rate {rate}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", help="only this business")
    parser.add_argument("--watch", action="store_true", help="refresh every 3 seconds")
    args = parser.parse_args()

    app = create_app("development")
    with app.app_context():
        if not args.watch:
            show(args.email)
            return

        try:
            while True:
                # EXPIRED FIRST. Without it SQLAlchemy serves the same
                # cached objects every loop and the numbers never move --
                # which looks exactly like a broken writer.
                db.session.expire_all()
                print("\033[2J\033[H", end="")
                print(time.strftime("%H:%M:%S"), "· ctrl-c to stop\n")
                show(args.email)
                time.sleep(3)
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()
