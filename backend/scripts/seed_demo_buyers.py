"""
Seed fake BUSINESSES and CONFIRMED orders against one supplier, so the
trust signals that need real trading history have something to show in
development.

WHY THIS EXISTS: several figures on the supplier profile and product
page are deliberately computed from DISTINCT businesses, not from order
counts -- "3 businesses buy this" means three different buyers, and one
account ordering fifty times is still one buyer. That's correct
behaviour (one loyal customer isn't fifty endorsements), but it makes
those figures impossible to see with a single business login. This
closes that gap with real rows through the real code path, rather than
lowering a threshold that exists for a good reason.

Everything it creates is tagged with SEED_EMAIL_PREFIX so `--undo`
can remove exactly what it added and nothing else.

    # A bare script does NOT auto-load .env the way the flask CLI
    # does, so the DB vars have to be exported first or it falls back
    # to the default postgres:postgres and fails to connect.
    set -a && source <(grep -E '^(SECRET_KEY|JWT_SECRET_KEY|POSTGRES_)' .env) && set +a
    .venv/Scripts/python.exe scripts/seed_demo_buyers.py --supplier-email you@example.com
    .venv/Scripts/python.exe scripts/seed_demo_buyers.py --supplier-email you@example.com --undo

DEV ONLY. It fabricates trading history; never point it at anything
real.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SEED_EMAIL_PREFIX = "seed-buyer-"
BUYER_COUNT = 4


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--supplier-email", required=True, help="The supplier account to seed buyers for.")
    parser.add_argument("--undo", action="store_true", help="Remove everything this script created.")
    args = parser.parse_args()

    from src import create_app
    from src.core.base_model import utcnow
    from src.domains.auth.models.user import AccountStatus, User, UserRole, VerificationStatus
    from src.domains.network.connections.models.connection_request import (
        ConnectionInitiatorRole,
        ConnectionRequest,
        ConnectionRequestStatus,
    )
    from src.domains.network.orders.models.stock_order import (
        StockOrder,
        StockOrderItem,
        StockOrderStatus,
    )
    from src.domains.supplier.products.repositories.product_repository import ProductRepository
    from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
        SupplierProfileRepository,
    )
    from src.extensions import db
    from src.shared.security.security import hash_password

    app = create_app("development")
    with app.app_context():
        supplier_user = User.query.filter_by(email=args.supplier_email).first()
        if supplier_user is None:
            print(f"No user with email {args.supplier_email}")
            return 1
        profile = SupplierProfileRepository.get_by_supplier_id(supplier_user.id)
        if profile is None:
            print("That user has no supplier profile (has it verified its email?)")
            return 1

        seeded = User.query.filter(User.email.like(f"{SEED_EMAIL_PREFIX}%")).all()

        if args.undo:
            ids = [u.id for u in seeded]
            if not ids:
                print("Nothing to undo.")
                return 0
            orders = StockOrder.query.filter(StockOrder.business_id.in_(ids)).all()
            for order in orders:
                StockOrderItem.query.filter_by(stock_order_id=order.id).delete()
            StockOrder.query.filter(StockOrder.business_id.in_(ids)).delete(synchronize_session=False)
            ConnectionRequest.query.filter(ConnectionRequest.business_id.in_(ids)).delete(
                synchronize_session=False
            )
            for user in seeded:
                db.session.delete(user)
            db.session.commit()
            print(f"Removed {len(seeded)} seeded buyers and their orders.")
            return 0

        products = ProductRepository.list_for_supplier(profile.id, is_archived=False)
        if not products:
            print("That supplier has no products to order.")
            return 1

        created = 0
        for index in range(BUYER_COUNT):
            email = f"{SEED_EMAIL_PREFIX}{index + 1}@example.com"
            buyer = User.query.filter_by(email=email).first()
            if buyer is None:
                buyer = User(
                    email=email,
                    password_hash=hash_password("SeedBuyer123!"),
                    role=UserRole.BUSINESS,
                    first_name=f"Seed Buyer {index + 1}",
                    business_name=f"Seed Buyer {index + 1} Trading",
                    account_status=AccountStatus.ACTIVE,
                    verification_status=VerificationStatus.VERIFIED,
                )
                db.session.add(buyer)
                db.session.flush()
                created += 1

            if not ConnectionRequest.query.filter_by(
                business_id=buyer.id, supplier_profile_id=profile.id
            ).first():
                db.session.add(
                    ConnectionRequest(
                        business_id=buyer.id,
                        supplier_profile_id=profile.id,
                        status=ConnectionRequestStatus.ACTIVE,
                        initiated_by_role=ConnectionInitiatorRole.BUSINESS,
                    )
                )

            # Each buyer orders a DIFFERENT slice of the catalogue, so
            # buyer counts vary per product rather than every product
            # showing the same number -- which is what real data looks
            # like, and what makes the "hidden below 3" rule visible.
            for product in products[: index + 2]:
                order = StockOrder(
                    business_id=buyer.id,
                    supplier_profile_id=profile.id,
                    status=StockOrderStatus.CONFIRMED,
                    total_cents=product.price_cents,
                    submitted_at=utcnow(),
                    decided_at=utcnow(),
                )
                db.session.add(order)
                db.session.flush()
                db.session.add(
                    StockOrderItem(
                        stock_order_id=order.id,
                        product_id=product.id,
                        quantity=1,
                        price_cents_at_add_time=product.price_cents,
                    )
                )

        db.session.commit()
        print(f"Seeded {BUYER_COUNT} buyers ({created} new) with CONFIRMED orders for {profile.business_name}.")
        print("Undo with:  python scripts/seed_demo_buyers.py --supplier-email "
              f"{args.supplier_email} --undo")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
