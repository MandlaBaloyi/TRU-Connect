"""
Orphan upload sweep tests.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.shared.media.intents.models import MediaUploadIntentStatus
from src.shared.media.intents.repositories import MediaUploadIntentRepository
from src.shared.media.intents.services import cancel_intent, create_intent, mark_registered
from src.shared.media.jobs import orphan_upload_sweep
from src.shared.media.providers.provider import MediaProvider, ScanResult, SignedUpload, UploadedAsset


class FakeMediaProvider(MediaProvider):
    def __init__(self):
        self.deleted: list = []

    def generate_signed_upload(self, public_id, max_dimension_px):
        raise NotImplementedError

    def upload_asset(self, public_id, file_bytes, max_dimension_px, resource_type="image"):
        raise NotImplementedError

    def verify_webhook_signature(self, raw_body, timestamp, signature):
        return True

    def parse_scan_result(self, payload):
        return ScanResult(public_id="", status="APPROVED", provider="fake")

    def delete_asset(self, public_id):
        self.deleted.append(public_id)


@pytest.fixture()
def fake_provider(monkeypatch):
    provider = FakeMediaProvider()
    monkeypatch.setattr(orphan_upload_sweep, "get_media_provider", lambda: provider)
    return provider


def _backdate(public_id: str, minutes_ago: int) -> None:
    intent = MediaUploadIntentRepository.get_by_public_id(public_id)
    intent.expires_at = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    from src.extensions import db

    db.session.commit()


def test_sweep_deletes_expired_issued_asset_and_marks_expired(fake_provider, db_session):
    account_id = uuid.uuid4()
    create_intent(account_id, "products", "tru_connect/suppliers/a/products/b/orphan")
    _backdate("tru_connect/suppliers/a/products/b/orphan", minutes_ago=5)

    result = orphan_upload_sweep.run()

    assert result.success is True
    assert result.count == 1
    assert "tru_connect/suppliers/a/products/b/orphan" in fake_provider.deleted
    intent = MediaUploadIntentRepository.get_by_public_id("tru_connect/suppliers/a/products/b/orphan")
    assert intent.status == MediaUploadIntentStatus.EXPIRED.value


def test_sweep_leaves_not_yet_expired_intents_alone(fake_provider, db_session):
    account_id = uuid.uuid4()
    create_intent(account_id, "products", "tru_connect/suppliers/a/products/b/fresh")

    result = orphan_upload_sweep.run()

    assert result.count == 0
    assert fake_provider.deleted == []


def test_sweep_leaves_registered_intents_alone_even_if_old(fake_provider, db_session):
    account_id = uuid.uuid4()
    create_intent(account_id, "products", "tru_connect/suppliers/a/products/b/registered")
    mark_registered("tru_connect/suppliers/a/products/b/registered")
    _backdate("tru_connect/suppliers/a/products/b/registered", minutes_ago=120)

    result = orphan_upload_sweep.run()

    assert result.count == 0
    assert fake_provider.deleted == []


def test_sweep_leaves_cancelled_intents_alone_even_if_old(fake_provider, db_session):
    account_id = uuid.uuid4()
    create_intent(account_id, "products", "tru_connect/suppliers/a/products/b/cancelled")
    cancel_intent("tru_connect/suppliers/a/products/b/cancelled")
    _backdate("tru_connect/suppliers/a/products/b/cancelled", minutes_ago=120)

    result = orphan_upload_sweep.run()

    assert result.count == 0
    assert fake_provider.deleted == []


def test_sweep_continues_past_a_delete_failure(fake_provider, db_session, monkeypatch):
    """A delete_asset failure for one orphan must not stop the sweep
    from cleaning up the rest."""
    account_id = uuid.uuid4()
    create_intent(account_id, "products", "tru_connect/suppliers/a/products/b/first")
    create_intent(account_id, "products", "tru_connect/suppliers/a/products/b/second")
    _backdate("tru_connect/suppliers/a/products/b/first", minutes_ago=5)
    _backdate("tru_connect/suppliers/a/products/b/second", minutes_ago=5)

    call_count = {"n": 0}
    original_delete = fake_provider.delete_asset

    def _flaky_delete(public_id):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("simulated Cloudinary failure")
        original_delete(public_id)

    monkeypatch.setattr(fake_provider, "delete_asset", _flaky_delete)

    result = orphan_upload_sweep.run()

    # Both marked expired regardless of which delete call failed --
    # the DB row is the source of truth for "resolved", not whether
    # the provider call happened to succeed.
    assert result.count == 2
    first = MediaUploadIntentRepository.get_by_public_id("tru_connect/suppliers/a/products/b/first")
    second = MediaUploadIntentRepository.get_by_public_id("tru_connect/suppliers/a/products/b/second")
    assert first.status == MediaUploadIntentStatus.EXPIRED.value
    assert second.status == MediaUploadIntentStatus.EXPIRED.value
