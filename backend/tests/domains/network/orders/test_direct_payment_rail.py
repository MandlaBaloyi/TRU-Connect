"""
The DIRECT payment rail, end to end.

WHY THIS FILE EXISTS. DIRECT replaced CASH and PROOF_OF_PAYMENT as the
one off-platform payment method, and it was added to the order enum and
to the database -- but not to the checkout request schema, not to the
provider composition, and not to the manual provider. The backend could
not complete a DIRECT checkout at all.

LATENT, NOT LIVE, and the distinction is worth stating plainly rather
than dressing this up. The mobile app still sends CASH and
PROOF_OF_PAYMENT -- its own PaymentMethod type does not include DIRECT
-- so no business ever hit this. It would have broken on the day the
frontend was switched over, which is the obvious next step of the work
that introduced DIRECT in the first place.

NOTHING CAUGHT IT, and the reason matters more than the bug. The
existing tests exercised DIRECT only on the REJECTION path, where the
spending cap fires before a provider is ever reached. A successful
DIRECT checkout had never once been run. So the first test here is the
plainest one imaginable -- place an order and have it succeed -- and it
goes through the HTTP route rather than calling the service directly,
because two of the three faults lived above the service layer.
"""
from __future__ import annotations

import pytest
from flask_jwt_extended import create_access_token

from src.domains.network.orders.models.stock_order import (
    DIRECT_PAYMENT_METHODS,
    StockOrderPaymentMethod,
    StockOrderStatus,
    is_direct_payment,
)
from src.domains.network.orders.providers.composition import get_payment_provider
from src.domains.network.orders.providers.manual_provider import ManualPaymentProvider
from src.domains.network.orders.services import cart_service, checkout_service


def test_a_direct_order_can_actually_be_placed(
    make_business, make_supplier, make_supplier_profile
):
    """The test whose absence let three separate faults ship."""
    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Direct Rail Co")
    product = _product(profile.id)
    cart_service.add_item(business.id, profile.id, product.id, 1)

    result = checkout_service.submit_checkout(business.id, profile.id, "DIRECT", "DELIVER")

    assert result["status"] == "PENDING_SUPPLIER_APPROVAL"
    assert result["orderReference"]


def test_the_http_route_accepts_direct(client, make_business, make_supplier, make_supplier_profile):
    """Two of the three faults were ABOVE the service layer -- the
    request schema rejected "DIRECT" outright with a validation error,
    so no amount of service-level testing would have found them."""
    business = make_business()
    profile = make_supplier_profile(make_supplier(), business_name="Direct Rail HTTP Co")
    product = _product(profile.id)
    cart_service.add_item(business.id, profile.id, product.id, 1)

    response = client.post(
        f"/api/v1/checkout/suppliers/{profile.id}/submit",
        json={"paymentMethod": "DIRECT", "deliveryType": "DELIVER", "deliveryAddressText": "12 Main Rd"},
        headers=_auth(business),
    )

    assert response.status_code == 200, response.get_json()
    assert response.get_json()["data"]["status"] == "PENDING_SUPPLIER_APPROVAL"


@pytest.mark.parametrize("method", [m.value for m in DIRECT_PAYMENT_METHODS])
def test_every_direct_method_routes_to_a_provider(method):
    """The routing fault, stated directly.

    get_payment_provider enumerated CASH and PROOF_OF_PAYMENT by hand,
    so DIRECT fell through to "no payment provider configured". Asking
    is_direct_payment instead of listing is what stops the next value
    from doing the same."""
    provider = get_payment_provider(StockOrderPaymentMethod(method))
    assert isinstance(provider, ManualPaymentProvider)


@pytest.mark.parametrize("method", [m.value for m in DIRECT_PAYMENT_METHODS])
def test_every_direct_method_produces_a_request_not_a_purchase(method):
    """PAYMENT METHOD SELECTS THE ORDER PATH (V2_00 section 2.4).

    Direct means the supplier is releasing stock against an unsecured
    promise, so the order is a REQUEST and their accept/decline is real.
    Accept/decline was never a supplier feature -- it is a consequence
    of cash, and a digital payment that has already moved the money
    skips it entirely."""
    outcome = ManualPaymentProvider().process_checkout(None, StockOrderPaymentMethod(method))

    assert outcome.order_status == StockOrderStatus.PENDING_SUPPLIER_APPROVAL
    assert outcome.instructions, "a direct order must tell the buyer how to pay"


def test_payfast_is_not_on_the_direct_rail():
    """The other half of the rule. A gateway payment is a PURCHASE: the
    money moved before the order existed, so there is nothing for the
    supplier to approve and nothing for the spending caps to bound."""
    assert not is_direct_payment(StockOrderPaymentMethod.PAYFAST)
    assert StockOrderPaymentMethod.PAYFAST not in DIRECT_PAYMENT_METHODS


def test_is_direct_payment_accepts_both_sides_of_the_wire():
    """A request schema hands over a string, a model column hands over
    the enum. Both callers exist, so both must work -- and an unknown
    string must be False rather than an exception, because it arrives
    from outside."""
    assert is_direct_payment("DIRECT") is True
    assert is_direct_payment(StockOrderPaymentMethod.DIRECT) is True
    assert is_direct_payment("PAYFAST") is False
    assert is_direct_payment("SOMETHING_ELSE") is False


def _auth(user) -> dict:
    """Same shape as products/test_products_api.py's own helper --
    duplicated per file, matching how every HTTP test in this codebase
    already does it."""
    token = create_access_token(identity=str(user.id), additional_claims={"role": "business"})
    return {"Authorization": f"Bearer {token}"}


def _product(profile_id, price_cents: int = 5000):
    from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
    from src.domains.supplier.products.algorithms.sku_generator import generate_sku
    from src.domains.supplier.products.models.supplier_offer import ProductCategory, ProductUnit
    from src.domains.supplier.products.repositories.supplier_offer_repository import (
        SupplierOfferRepository,
    )

    from src.domains.supplier.inventory.repositories.inventory_repository import (
        InventoryRepository,
    )

    product = SupplierOfferRepository.create(
        profile_id,
        "Bread",
        ProductCategory.BAKERY,
        price_cents,
        ProductUnit.EACH,
        sku=generate_sku(profile_id),
        product_code=generate_product_code(),
    )
    # Stock is required or the cart refuses the item -- same seeding
    # test_cart_and_checkout.py's own _make_product does.
    inventory = InventoryRepository.get_or_create_for_product(product.id, profile_id)
    InventoryRepository.adjust_quantity(inventory, 100)
    return product
