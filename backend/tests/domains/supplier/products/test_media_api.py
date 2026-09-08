"""
SupplierOffer media HTTP-layer tests, same pattern as test_products_api.py.
FakeMediaProvider is duplicated here rather than imported from
test_product_media_service.py -- this codebase has no top-level
tests/__init__.py, so cross-test-file imports aren't reliable; small
test doubles get their own copy per file, same pragmatism as this
codebase's own conftest.py fixture duplication across domains.
"""
from __future__ import annotations

from flask_jwt_extended import create_access_token

from src.domains.supplier.products.models.supplier_offer import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository
from src.domains.supplier.products.services import product_media_service
from src.shared.media import folder_naming
from src.shared.media.providers.provider import MediaProvider, ScanResult, SignedUpload


class FakeMediaProvider(MediaProvider):
    def __init__(self):
        self.deleted_public_ids: list[str] = []

    def upload_asset(self, public_id, file_bytes, max_dimension_px=1600, asset_folder="tru_connect/fake", resource_type="image"):
        from src.shared.media.providers.provider import UploadedAsset
        return UploadedAsset(
            public_id=public_id,
            secure_url=f"https://res.cloudinary.com/test/{public_id}.jpg",
            resource_type=resource_type,
            format="jpg",
            width=800,
            height=600,
            bytes=len(file_bytes),
        )

    def generate_signed_upload(self, public_id: str, max_dimension_px: int = 1600, asset_folder: str = "tru_connect/fake") -> SignedUpload:
        return SignedUpload(
            cloud_name="test_cloud",
            api_key="test_key",
            timestamp=1_700_000_000,
            signature="fake_signature",
            public_id=public_id,
            upload_url="https://api.cloudinary.com/v1_1/test_cloud/image/upload",
            allowed_formats="jpg,jpeg,png,webp",
            transformation="c_limit,w_1600,h_1600,q_auto",
            notification_url="",
            moderation="perception_point",
            asset_folder=asset_folder,
        )

    def verify_webhook_signature(self, raw_body: str, timestamp: str, signature: str) -> bool:
        return signature == "valid_signature"

    def parse_scan_result(self, payload: dict) -> ScanResult:
        return ScanResult(public_id=payload["public_id"], status=payload["status"], provider="fake")

    def delete_asset(self, public_id: str) -> None:
        self.deleted_public_ids.append(public_id)

    def delete_assets(self, public_ids) -> None:
        self.deleted_public_ids.extend(public_ids)

    def delete_folder(self, folder_path: str) -> None:
        pass

    def is_moderation_enabled(self) -> bool:
        return True


def _token_for(user, role: str) -> str:
    return create_access_token(identity=str(user.id), additional_claims={"role": role})


def _auth(user, role: str) -> dict:
    return {"Authorization": f"Bearer {_token_for(user, role)}"}


def _make_product(profile_id, **overrides):
    from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
    from src.domains.supplier.products.algorithms.sku_generator import generate_sku

    defaults = dict(
        supplier_profile_id=profile_id,
        name="Coca-Cola 500ml",
        category=ProductCategory.BEVERAGES,
        price_cents=1200,
        selling_unit=ProductUnit.EACH,
        sku=generate_sku(profile_id),
        product_code=generate_product_code(),
    )
    defaults.update(overrides)
    return SupplierOfferRepository.create(**defaults)


def _patch_provider(monkeypatch) -> FakeMediaProvider:
    provider = FakeMediaProvider()
    monkeypatch.setattr(product_media_service, "get_media_provider", lambda: provider)
    return provider


def test_request_upload_signature_via_http(client, monkeypatch, make_supplier, make_supplier_profile):
    _patch_provider(monkeypatch)
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    response = client.post(
        f"/api/v1/supplier-discovery/products/{product.id}/media/upload-signature",
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["cloud_name"]
    assert "api_secret" not in data  # the whole point


def test_request_upload_signature_not_found_for_other_suppliers_product(
    client, monkeypatch, make_supplier, make_supplier_profile
):
    _patch_provider(monkeypatch)
    owner = make_supplier("media-http-owner@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Media HTTP Owner")
    other = make_supplier("media-http-other@example.com")
    make_supplier_profile(other, business_name="Media HTTP Other")
    product = _make_product(owner_profile.id)

    response = client.post(
        f"/api/v1/supplier-discovery/products/{product.id}/media/upload-signature",
        headers=_auth(other, "supplier"),
    )

    assert response.status_code == 404


def test_register_media_via_http(client, monkeypatch, make_supplier, make_supplier_profile):
    _patch_provider(monkeypatch)
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    public_id = folder_naming.supplier_product_folder(profile.id, product.id) + "/asset1"

    response = client.post(
        f"/api/v1/supplier-discovery/products/{product.id}/media",
        json={
            "cloudinary_public_id": public_id,
            "secure_url": "https://res.cloudinary.com/x/asset1.jpg",
            "resource_type": "image",
            "format": "jpg",
            "width": 800,
            "height": 600,
            "bytes": 50000,
        },
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["scan_status"] == "PENDING"


def test_register_media_rejects_wrong_folder_public_id_via_http(
    client, monkeypatch, make_supplier, make_supplier_profile
):
    _patch_provider(monkeypatch)
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)

    response = client.post(
        f"/api/v1/supplier-discovery/products/{product.id}/media",
        json={
            "cloudinary_public_id": "tru_connect/suppliers/not-this-supplier/products/not-this-product/hacked",
            "secure_url": "https://x/hacked.jpg",
        },
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 404


def test_business_role_rejected_from_media_endpoints(client, make_business):
    business = make_business()

    response = client.post(
        "/api/v1/supplier-discovery/products/00000000-0000-0000-0000-000000000000/media/upload-signature",
        headers=_auth(business, "business"),
    )

    assert response.status_code == 403


# --- Webhook -------------------------------------------------------------


def test_webhook_rejects_invalid_signature(client):
    response = client.post(
        "/api/v1/media/webhooks/cloudinary-notifications",
        json={"public_id": "tru_connect/suppliers/x/products/y/z", "moderation_status": "approved"},
        headers={"X-Cld-Timestamp": "123", "X-Cld-Signature": "not_real"},
    )

    assert response.status_code == 401


def test_webhook_approves_media_end_to_end(client, monkeypatch, make_supplier, make_supplier_profile):
    """Real HTTP request through the real route, real signature
    verification (via a fake provider that accepts "valid_signature"),
    real DB update -- the fullest end-to-end proof available without
    actual network access to Cloudinary."""
    fake = _patch_provider(monkeypatch)
    monkeypatch.setattr("src.shared.media.webhooks.webhook_service.get_media_provider", lambda: fake)

    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    product = _make_product(profile.id)
    public_id = folder_naming.supplier_product_folder(profile.id, product.id) + "/webhook-test"
    client.post(
        f"/api/v1/supplier-discovery/products/{product.id}/media",
        json={"cloudinary_public_id": public_id, "secure_url": "https://x/webhook-test.jpg"},
        headers=_auth(supplier, "supplier"),
    )

    response = client.post(
        "/api/v1/media/webhooks/cloudinary-notifications",
        json={"public_id": public_id, "status": "APPROVED"},
        headers={"X-Cld-Timestamp": "123", "X-Cld-Signature": "valid_signature"},
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "APPROVED"

    urls = product_media_service.list_approved_media(product.id)
    assert urls == ["https://x/webhook-test.jpg"]
