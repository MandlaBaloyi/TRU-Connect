"""
Bulk import HTTP-layer tests. Monkeypatches src.shared.queue.queue.
enqueue to run the job SYNCHRONOUSLY (call it immediately instead of
deferring to a background thread) -- makes these tests deterministic
without sleeping/polling for a real background thread to finish.

FakeMediaProvider is duplicated here rather than imported from
test_import_worker.py -- this codebase has no top-level
tests/__init__.py, so cross-test-file imports aren't reliable, same
reasoning as test_media_api.py's own docstring.
"""
from __future__ import annotations

import io
import zipfile

from flask_jwt_extended import create_access_token

from src.domains.supplier.products.repositories.product_repository import ProductRepository
from src.shared.media.providers.provider import MediaProvider, ScanResult, SignedUpload, UploadedAsset


class FakeMediaProvider(MediaProvider):
    def generate_signed_upload(self, public_id: str, max_dimension_px: int = 1600) -> SignedUpload:
        raise NotImplementedError("bulk import never uses the signed-client-upload path")

    def upload_asset(self, public_id: str, file_bytes: bytes, max_dimension_px: int = 1600, resource_type: str = "image") -> UploadedAsset:
        return UploadedAsset(
            public_id=public_id,
            secure_url=f"https://res.cloudinary.com/test/{public_id}.jpg",
            resource_type=resource_type,
            format="jpg",
            width=800,
            height=600,
            bytes=len(file_bytes),
        )

    def verify_webhook_signature(self, raw_body: str, timestamp: str, signature: str) -> bool:
        return True

    def parse_scan_result(self, payload: dict) -> ScanResult:
        return ScanResult(public_id=payload.get("public_id", ""), status="APPROVED", provider="fake")

    def delete_asset(self, public_id: str) -> None:
        pass


def _token_for(user, role: str) -> str:
    return create_access_token(identity=str(user.id), additional_claims={"role": role})


def _auth(user, role: str) -> dict:
    return {"Authorization": f"Bearer {_token_for(user, role)}"}


def _synchronous_enqueue(monkeypatch):
    def _run_now(job):
        job()

    monkeypatch.setattr("src.shared.queue.queue.enqueue", _run_now)


def test_submit_import_returns_202_and_job_is_completed_on_poll(
    client, monkeypatch, make_supplier, make_supplier_profile
):
    """The POST response itself reflects state AT CREATION TIME
    (UPLOADED) -- correct 202-Accepted semantics, since in production
    the worker runs on a genuinely separate thread that may not have
    started yet. Even with the synchronous-in-test enqueue patch, the
    worker runs inside its OWN app_context() with its own session
    scope, so the route's own in-memory job object correctly doesn't
    reflect it -- a SEPARATE poll (its own fresh session/request) does,
    which is exactly the real client-facing pattern this endpoint is
    designed around."""
    _synchronous_enqueue(monkeypatch)
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    csv_bytes = b"name,category,price,unit,quantity\nCoca-Cola 500ml,Beverages,12.00,Each,47\n"

    response = client.post(
        "/api/v1/supplier-discovery/imports",
        data={"spreadsheet": (io.BytesIO(csv_bytes), "products.csv")},
        content_type="multipart/form-data",
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 202
    job_id = response.get_json()["data"]["id"]

    poll = client.get(f"/api/v1/supplier-discovery/imports/{job_id}", headers=_auth(supplier, "supplier"))
    data = poll.get_json()["data"]
    assert data["status"] == "COMPLETED"
    assert data["created_rows"] == 1

    products = ProductRepository.list_for_supplier(profile.id)
    assert len(products) == 1


def test_submit_import_requires_a_spreadsheet_file(client, make_supplier, make_supplier_profile):
    supplier = make_supplier()
    make_supplier_profile(supplier)

    response = client.post(
        "/api/v1/supplier-discovery/imports",
        data={},
        content_type="multipart/form-data",
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 422


def test_get_import_returns_job_status(client, monkeypatch, make_supplier, make_supplier_profile):
    _synchronous_enqueue(monkeypatch)
    supplier = make_supplier()
    make_supplier_profile(supplier)
    csv_bytes = b"name,category,price,unit\nBread,Bakery,19.99,Each\n"
    submit = client.post(
        "/api/v1/supplier-discovery/imports",
        data={"spreadsheet": (io.BytesIO(csv_bytes), "products.csv")},
        content_type="multipart/form-data",
        headers=_auth(supplier, "supplier"),
    )
    job_id = submit.get_json()["data"]["id"]

    response = client.get(f"/api/v1/supplier-discovery/imports/{job_id}", headers=_auth(supplier, "supplier"))

    assert response.status_code == 200
    assert response.get_json()["data"]["id"] == job_id


def test_get_import_not_found_for_other_suppliers_job(client, monkeypatch, make_supplier, make_supplier_profile):
    _synchronous_enqueue(monkeypatch)
    owner = make_supplier("bulk-owner@example.com")
    make_supplier_profile(owner, business_name="Bulk Owner Co")
    other = make_supplier("bulk-other@example.com")
    make_supplier_profile(other, business_name="Bulk Other Co")
    csv_bytes = b"name,category,price,unit\nBread,Bakery,19.99,Each\n"
    submit = client.post(
        "/api/v1/supplier-discovery/imports",
        data={"spreadsheet": (io.BytesIO(csv_bytes), "products.csv")},
        content_type="multipart/form-data",
        headers=_auth(owner, "supplier"),
    )
    job_id = submit.get_json()["data"]["id"]

    response = client.get(f"/api/v1/supplier-discovery/imports/{job_id}", headers=_auth(other, "supplier"))

    assert response.status_code == 404


def test_get_import_errors_returns_row_level_errors(client, monkeypatch, make_supplier, make_supplier_profile):
    _synchronous_enqueue(monkeypatch)
    supplier = make_supplier()
    make_supplier_profile(supplier)
    csv_bytes = b"name,category,price,unit\nBad Row,NotARealCategory,12.00,Each\n"
    submit = client.post(
        "/api/v1/supplier-discovery/imports",
        data={"spreadsheet": (io.BytesIO(csv_bytes), "products.csv")},
        content_type="multipart/form-data",
        headers=_auth(supplier, "supplier"),
    )
    job_id = submit.get_json()["data"]["id"]

    response = client.get(
        f"/api/v1/supplier-discovery/imports/{job_id}/errors", headers=_auth(supplier, "supplier")
    )

    assert response.status_code == 200
    errors = response.get_json()["data"]["results"]
    assert len(errors) == 1
    assert errors[0]["row_number"] == 2
    assert errors[0]["field"] == "category"


def test_list_imports_returns_history(client, monkeypatch, make_supplier, make_supplier_profile):
    _synchronous_enqueue(monkeypatch)
    supplier = make_supplier()
    make_supplier_profile(supplier)
    csv_bytes = b"name,category,price,unit\nBread,Bakery,19.99,Each\n"
    client.post(
        "/api/v1/supplier-discovery/imports",
        data={"spreadsheet": (io.BytesIO(csv_bytes), "products.csv")},
        content_type="multipart/form-data",
        headers=_auth(supplier, "supplier"),
    )

    response = client.get("/api/v1/supplier-discovery/imports", headers=_auth(supplier, "supplier"))

    assert response.status_code == 200
    assert len(response.get_json()["data"]["results"]) == 1


def test_business_role_is_rejected(client, make_business):
    business = make_business()

    response = client.post(
        "/api/v1/supplier-discovery/imports",
        data={},
        content_type="multipart/form-data",
        headers=_auth(business, "business"),
    )

    assert response.status_code == 403


def test_unauthenticated_request_is_rejected(client):
    response = client.post("/api/v1/supplier-discovery/imports", data={}, content_type="multipart/form-data")

    assert response.status_code == 401


def test_submit_with_real_zip_via_http(client, monkeypatch, make_supplier, make_supplier_profile):
    _synchronous_enqueue(monkeypatch)
    from src.domains.supplier.products.services import product_media_service

    fake = FakeMediaProvider()
    monkeypatch.setattr(product_media_service, "get_media_provider", lambda: fake)

    supplier = make_supplier()
    make_supplier_profile(supplier)
    csv_bytes = b"name,category,price,unit,image_1\nCoca-Cola 500ml,Beverages,12.00,Each,coke500.jpg\n"

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("coke500.jpg", b"real jpeg data")
    zip_buf.seek(0)

    response = client.post(
        "/api/v1/supplier-discovery/imports",
        data={
            "spreadsheet": (io.BytesIO(csv_bytes), "products.csv"),
            "zip": (zip_buf, "images.zip"),
        },
        content_type="multipart/form-data",
        headers=_auth(supplier, "supplier"),
    )

    assert response.status_code == 202
    job_id = response.get_json()["data"]["id"]

    poll = client.get(f"/api/v1/supplier-discovery/imports/{job_id}", headers=_auth(supplier, "supplier"))
    data = poll.get_json()["data"]
    assert data["status"] == "COMPLETED"
    assert data["images_matched"] == 1
