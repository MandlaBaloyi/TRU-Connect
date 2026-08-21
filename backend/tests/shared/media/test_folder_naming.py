"""
folder_naming.py tests -- the builder and the matcher must agree with
each other, or webhook dispatch silently breaks for every real upload.
"""
from __future__ import annotations

from src.shared.media import folder_naming


def test_supplier_product_folder_shape():
    folder = folder_naming.supplier_product_folder("sup-123", "prod-456")
    assert folder == "tru_connect/suppliers/sup-123/products/prod-456"


def test_matcher_recognises_a_real_built_folder():
    folder = folder_naming.supplier_product_folder("sup-123", "prod-456")
    public_id = f"{folder}/some-asset-uuid"

    assert folder_naming.is_supplier_product_asset(public_id) is True


def test_matcher_rejects_a_non_product_path():
    assert folder_naming.is_supplier_product_asset("tru_connect/suppliers/sup-123/profile/asset") is False
    assert folder_naming.is_supplier_product_asset("tru_connect/businesses/biz-1/documents/asset") is False
