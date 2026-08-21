"""
Upload ledger tests -- the cross-domain accounting/safety-net piece.
"""
from __future__ import annotations

import uuid

import pytest

from src.shared.media.errors import MediaUploadQuotaExceededError
from src.shared.media.ledger.services import DAILY_ACCOUNT_BYTE_QUOTA, check_quota_before_upload, record_upload


def test_record_and_sum_across_multiple_domains(db_session):
    """The whole point of this table -- ONE account's usage summed
    across domains that don't know about each other."""
    account_id = uuid.uuid4()
    record_upload(account_id, "products", 10 * 1024 * 1024)
    record_upload(account_id, "profile", 5 * 1024 * 1024)

    # A quota check just under the combined total should fail.
    with pytest.raises(MediaUploadQuotaExceededError):
        check_quota_before_upload(account_id, DAILY_ACCOUNT_BYTE_QUOTA - (15 * 1024 * 1024) + 1)


def test_quota_check_passes_when_comfortably_under(db_session):
    account_id = uuid.uuid4()
    record_upload(account_id, "products", 1024)

    # Should not raise.
    check_quota_before_upload(account_id, 1024)


def test_different_accounts_do_not_share_quota(db_session):
    account_a = uuid.uuid4()
    account_b = uuid.uuid4()
    record_upload(account_a, "products", DAILY_ACCOUNT_BYTE_QUOTA)

    # account_b's own usage is untouched by account_a's -- should not raise.
    check_quota_before_upload(account_b, 1024)
