"""
folder_naming.py tests -- the builder and the matcher must agree with
each other, or webhook dispatch silently breaks for every real upload.
"""
from __future__ import annotations

import os

from src.shared.media import folder_naming


def test_supplier_product_folder_shape():
    folder = folder_naming.supplier_product_folder("sup-123", "prod-456")

    assert folder.startswith("tru_connect/suppliers/")
    assert "/products/" in folder


def test_real_ids_never_appear_in_the_built_folder_path():
    """THE ACTUAL FIX found during a security review: a real
    supplier_profile_id or product_id sitting directly in a
    third-party vendor's own folder tree is an unnecessary information
    exposure, even though it was never independently exploitable on
    its own (ownership is always enforced by a signed JWT plus a real
    database check, never by an ID staying secret)."""
    real_supplier_id = "100116cd-4fb6-4f5e-94be-169f306c7928"
    real_product_id = "ac649b76-cf87-4afd-96cb-b93f4ec3236c"

    folder = folder_naming.supplier_product_folder(real_supplier_id, real_product_id)

    assert real_supplier_id not in folder
    assert real_product_id not in folder


def test_obscured_folder_is_deterministic_so_ownership_checks_keep_working():
    """The SAME real ID must always produce the SAME obscured value --
    this is what lets register_uploaded_media's own ownership check
    (which independently rebuilds the expected path and compares it)
    keep working completely unchanged: both the original build and the
    later verification call this exact same function."""
    folder1 = folder_naming.supplier_product_folder("sup-123", "prod-456")
    folder2 = folder_naming.supplier_product_folder("sup-123", "prod-456")

    assert folder1 == folder2


def test_different_real_ids_produce_different_obscured_values():
    folder_a = folder_naming.supplier_product_folder("sup-123", "prod-456")
    folder_b = folder_naming.supplier_product_folder("sup-123", "prod-DIFFERENT")
    folder_c = folder_naming.supplier_product_folder("sup-DIFFERENT", "prod-456")

    assert folder_a != folder_b
    assert folder_a != folder_c


def test_obscuring_depends_on_the_real_secret_key(monkeypatch):
    """Confirms this is a genuine HMAC keyed on SECRET_KEY, not just an
    unkeyed hash -- a different secret must produce a different
    obscured value for the exact same real ID."""
    monkeypatch.setenv("SECRET_KEY", "first-test-secret")
    folder_with_first_secret = folder_naming.supplier_product_folder("sup-123", "prod-456")

    monkeypatch.setenv("SECRET_KEY", "a-completely-different-test-secret")
    folder_with_second_secret = folder_naming.supplier_product_folder("sup-123", "prod-456")

    assert folder_with_first_secret != folder_with_second_secret


def test_matcher_recognises_a_real_built_folder():
    folder = folder_naming.supplier_product_folder("sup-123", "prod-456")
    public_id = f"{folder}/some-asset-uuid"

    assert folder_naming.is_supplier_product_asset(public_id) is True


def test_matcher_rejects_a_non_product_path():
    assert folder_naming.is_supplier_product_asset("tru_connect/suppliers/sup-123/profile/asset") is False
    assert folder_naming.is_supplier_product_asset("tru_connect/businesses/biz-1/documents/asset") is False
