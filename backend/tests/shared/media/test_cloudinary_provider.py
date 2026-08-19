"""
CloudinaryMediaProvider tests -- real HMAC signing/verification, no
mocking of the crypto itself. This environment cannot reach
api.cloudinary.com (confirmed directly against this sandbox's own
network policy before writing this file), but that's irrelevant here:
signing and webhook verification are BOTH local computation, no
network call involved -- see cloudinary_provider.py's own docstring.
Only the client's own direct-to-Cloudinary upload (never touched by
this backend) is the genuinely networked half.
"""
from __future__ import annotations

import hashlib
import time

import pytest

from src.shared.media.config import MediaConfig
from src.shared.media.cloudinary_provider import CloudinaryMediaProvider


@pytest.fixture()
def config() -> MediaConfig:
    return MediaConfig(cloud_name="test_cloud", api_key="test_key_123", api_secret="test_secret_abc")


@pytest.fixture()
def provider(config) -> CloudinaryMediaProvider:
    return CloudinaryMediaProvider(config)


def _real_webhook_signature(body: str, timestamp: str, api_secret: str) -> str:
    """Computes a signature the EXACT way Cloudinary itself does --
    confirmed directly against the installed SDK's own
    verify_notification_signature source before writing this helper,
    not assumed from documentation alone."""
    return hashlib.sha1(f"{body}{timestamp}{api_secret}".encode("utf-8")).hexdigest()


class TestGenerateSignedUpload:
    def test_signed_upload_contains_expected_fields(self, provider, config):
        signed = provider.generate_signed_upload("tru_connect/products/sup1/prod1/asset1")

        assert signed.cloud_name == config.cloud_name
        assert signed.api_key == config.api_key
        assert signed.public_id == "tru_connect/products/sup1/prod1/asset1"
        assert signed.signature  # non-empty
        assert signed.timestamp > 0
        assert "jpg" in signed.allowed_formats

    def test_api_secret_never_appears_in_the_signed_upload(self, provider, config):
        """The one property that matters most -- the secret must never
        leave this process."""
        signed = provider.generate_signed_upload("tru_connect/products/sup1/prod1/asset1")

        serialized = str(signed)
        assert config.api_secret not in serialized

    def test_different_public_ids_produce_different_signatures(self, provider):
        first = provider.generate_signed_upload("tru_connect/products/sup1/prod1/asset1")
        second = provider.generate_signed_upload("tru_connect/products/sup1/prod2/asset2")

        assert first.signature != second.signature


class TestVerifyWebhookSignature:
    def test_accepts_a_genuinely_correctly_signed_request(self, provider, config):
        body = '{"public_id": "tru_connect/products/sup1/prod1/asset1", "moderation_status": "approved"}'
        timestamp = str(int(time.time()))
        real_signature = _real_webhook_signature(body, timestamp, config.api_secret)

        assert provider.verify_webhook_signature(body, timestamp, real_signature) is True

    def test_rejects_a_tampered_signature(self, provider):
        body = '{"public_id": "tru_connect/products/sup1/prod1/asset1", "moderation_status": "approved"}'
        timestamp = str(int(time.time()))

        assert provider.verify_webhook_signature(body, timestamp, "not_the_real_signature") is False

    def test_rejects_when_body_was_modified_after_signing(self, provider, config):
        """Proves the signature actually covers the BODY content, not
        just timestamp+secret -- a tampered body with the ORIGINAL
        signature must still fail."""
        original_body = '{"public_id": "tru_connect/products/sup1/prod1/asset1", "moderation_status": "approved"}'
        timestamp = str(int(time.time()))
        signature_for_original = _real_webhook_signature(original_body, timestamp, config.api_secret)

        tampered_body = '{"public_id": "tru_connect/products/sup1/prod1/asset1", "moderation_status": "rejected"}'

        assert provider.verify_webhook_signature(tampered_body, timestamp, signature_for_original) is False

    def test_rejects_an_expired_timestamp(self, provider, config):
        body = '{"public_id": "asset1", "moderation_status": "approved"}'
        old_timestamp = str(int(time.time()) - 10_000)  # well past signature_valid_for_seconds
        real_signature = _real_webhook_signature(body, old_timestamp, config.api_secret)

        assert provider.verify_webhook_signature(body, old_timestamp, real_signature) is False

    def test_rejects_missing_signature_or_timestamp(self, provider):
        assert provider.verify_webhook_signature("{}", "", "somesig") is False
        assert provider.verify_webhook_signature("{}", "123", "") is False


class TestParseScanResult:
    def test_parses_flat_moderation_status_shape(self, provider):
        result = provider.parse_scan_result({"public_id": "asset1", "moderation_status": "approved"})

        assert result.status == "APPROVED"
        assert result.public_id == "asset1"
        assert result.provider == "cloudinary"

    def test_parses_rejected(self, provider):
        result = provider.parse_scan_result({"public_id": "asset1", "moderation_status": "rejected"})

        assert result.status == "REJECTED"

    def test_parses_moderation_array_shape(self, provider):
        """The other real, documented Cloudinary payload shape -- see
        cloudinary_provider.py's own docstring on why both are handled."""
        result = provider.parse_scan_result({"public_id": "asset1", "moderation": [{"status": "approved"}]})

        assert result.status == "APPROVED"

    def test_unrecognised_status_maps_to_error_not_a_crash(self, provider):
        result = provider.parse_scan_result({"public_id": "asset1", "moderation_status": "something_new"})

        assert result.status == "ERROR"

    def test_missing_status_entirely_maps_to_error(self, provider):
        result = provider.parse_scan_result({"public_id": "asset1"})

        assert result.status == "ERROR"
