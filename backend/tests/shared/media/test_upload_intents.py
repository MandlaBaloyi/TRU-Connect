"""
Upload intent tests -- the orphan-upload protection piece.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from src.shared.media.intents.models import MediaUploadIntentStatus
from src.shared.media.intents.repositories import MediaUploadIntentRepository
from src.shared.media.intents.services import cancel_intent, create_intent, mark_registered


def test_create_intent_starts_issued(db_session):
    account_id = uuid.uuid4()

    intent = create_intent(account_id, "products", "tru_connect/suppliers/x/products/y/z")

    assert intent.status == MediaUploadIntentStatus.ISSUED.value
    assert intent.registered_at is None
    assert intent.expires_at > datetime.now(timezone.utc)


def test_mark_registered_moves_status_and_sets_timestamp(db_session):
    account_id = uuid.uuid4()
    create_intent(account_id, "products", "tru_connect/suppliers/x/products/y/z")

    mark_registered("tru_connect/suppliers/x/products/y/z")

    intent = MediaUploadIntentRepository.get_by_public_id("tru_connect/suppliers/x/products/y/z")
    assert intent.status == MediaUploadIntentStatus.REGISTERED.value
    assert intent.registered_at is not None


def test_mark_registered_for_unknown_public_id_is_a_safe_no_op(db_session):
    """Bulk import's own upload path never creates an intent at all --
    calling mark_registered for a public_id with no intent must not
    raise."""
    mark_registered("tru_connect/suppliers/never/products/registered/anything")


def test_cancel_intent_moves_status_to_cancelled(db_session):
    account_id = uuid.uuid4()
    create_intent(account_id, "products", "tru_connect/suppliers/x/products/y/z")

    cancel_intent("tru_connect/suppliers/x/products/y/z")

    intent = MediaUploadIntentRepository.get_by_public_id("tru_connect/suppliers/x/products/y/z")
    assert intent.status == MediaUploadIntentStatus.CANCELLED.value


def test_list_expired_still_issued_excludes_registered_and_cancelled(db_session):
    account_id = uuid.uuid4()
    issued = create_intent(account_id, "products", "tru_connect/suppliers/a/products/b/issued")
    registered = create_intent(account_id, "products", "tru_connect/suppliers/a/products/b/registered")
    cancelled = create_intent(account_id, "products", "tru_connect/suppliers/a/products/b/cancelled")

    # Backdate all three past "now" so they'd all be candidates for
    # expiry if status didn't matter.
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    for intent in (issued, registered, cancelled):
        intent.expires_at = past
    mark_registered("tru_connect/suppliers/a/products/b/registered")
    cancel_intent("tru_connect/suppliers/a/products/b/cancelled")

    expired_candidates = MediaUploadIntentRepository.list_expired_still_issued(datetime.now(timezone.utc))

    public_ids = {i.cloudinary_public_id for i in expired_candidates}
    assert public_ids == {"tru_connect/suppliers/a/products/b/issued"}


def test_list_expired_still_issued_excludes_not_yet_expired(db_session):
    account_id = uuid.uuid4()
    create_intent(account_id, "products", "tru_connect/suppliers/a/products/b/not-expired-yet")

    expired_candidates = MediaUploadIntentRepository.list_expired_still_issued(datetime.now(timezone.utc))

    assert expired_candidates == []
