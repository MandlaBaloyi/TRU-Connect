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

from src.shared.media.config.media_config import MediaConfig
from src.shared.media.providers.cloudinary_provider import CloudinaryMediaProvider


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
        signed = provider.generate_signed_upload("tru_connect/suppliers/sup1/products/prod1/asset1", 1600)

        assert signed.cloud_name == config.cloud_name
        assert signed.api_key == config.api_key
        assert signed.public_id == "tru_connect/suppliers/sup1/products/prod1/asset1"
        assert signed.signature  # non-empty
        assert signed.timestamp > 0
        assert "jpg" in signed.allowed_formats

    def test_api_secret_never_appears_in_the_signed_upload(self, provider, config):
        """The one property that matters most -- the secret must never
        leave this process."""
        signed = provider.generate_signed_upload("tru_connect/suppliers/sup1/products/prod1/asset1", 1600)

        serialized = str(signed)
        assert config.api_secret not in serialized

    def test_different_public_ids_produce_different_signatures(self, provider):
        first = provider.generate_signed_upload("tru_connect/suppliers/sup1/products/prod1/asset1", 1600)
        second = provider.generate_signed_upload("tru_connect/suppliers/sup1/products/prod2/asset2", 1600)

        assert first.signature != second.signature


class TestVerifyWebhookSignature:
    def test_accepts_a_genuinely_correctly_signed_request(self, provider, config):
        body = '{"public_id": "tru_connect/suppliers/sup1/products/prod1/asset1", "moderation_status": "approved"}'
        timestamp = str(int(time.time()))
        real_signature = _real_webhook_signature(body, timestamp, config.api_secret)

        assert provider.verify_webhook_signature(body, timestamp, real_signature) is True

    def test_rejects_a_tampered_signature(self, provider):
        body = '{"public_id": "tru_connect/suppliers/sup1/products/prod1/asset1", "moderation_status": "approved"}'
        timestamp = str(int(time.time()))

        assert provider.verify_webhook_signature(body, timestamp, "not_the_real_signature") is False

    def test_rejects_when_body_was_modified_after_signing(self, provider, config):
        """Proves the signature actually covers the BODY content, not
        just timestamp+secret -- a tampered body with the ORIGINAL
        signature must still fail."""
        original_body = '{"public_id": "tru_connect/suppliers/sup1/products/prod1/asset1", "moderation_status": "approved"}'
        timestamp = str(int(time.time()))
        signature_for_original = _real_webhook_signature(original_body, timestamp, config.api_secret)

        tampered_body = '{"public_id": "tru_connect/suppliers/sup1/products/prod1/asset1", "moderation_status": "rejected"}'

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
        """Distinct from IGNORED below -- notification_type explicitly
        says "moderation" here, so this genuinely claims to be a real
        scan result; an unrecognised status inside it is a real ERROR,
        not something to silently ignore."""
        result = provider.parse_scan_result(
            {"public_id": "asset1", "notification_type": "moderation", "moderation_status": "something_new"}
        )

        assert result.status == "ERROR"

    def test_upload_notification_is_ignored_not_misfiled_as_error(self, provider):
        """The actual bug found during real device testing: Cloudinary
        calls the SAME notification_url for its "upload" notification
        (fires the instant a file lands, before scanning) as it does
        for a real moderation result. This payload shape is the real
        one captured from that test, trimmed to the fields that
        matter -- no moderation_status, notification_type: "upload".
        Must be IGNORED, never ERROR -- nothing failed a scan; no scan
        has happened yet."""
        real_upload_notification_payload = {
            "notification_type": "upload",
            "timestamp": "2026-08-21T16:22:10+00:00",
            "public_id": "tru_connect/suppliers/sup1/products/prod1/asset1",
            "format": "jpg",
            "resource_type": "image",
            "bytes": 36486,
            "secure_url": "https://res.cloudinary.com/f5fbqhac/image/upload/v1/asset1.jpg",
        }

        result = provider.parse_scan_result(real_upload_notification_payload)

        assert result.status == "IGNORED"
        assert result.public_id == "tru_connect/suppliers/sup1/products/prod1/asset1"

    def test_missing_status_and_missing_notification_type_is_ignored(self, provider):
        """A minimal/unrecognisable payload with no moderation
        information at all, and nothing claiming to be a moderation
        result -- IGNORED, not ERROR, per the same reasoning above."""
        result = provider.parse_scan_result({"public_id": "asset1"})

        assert result.status == "IGNORED"


class TestNotificationUrl:
    """The webhook-wiring bug found during real device testing: a
    signed upload that never told Cloudinary where to send its scan
    result meant every photo stayed PENDING forever, invisible in the
    app, even though the upload itself succeeded. Covers both real
    states this can be in."""

    def test_included_when_webhook_base_url_is_configured(self):
        config = MediaConfig(
            cloud_name="test_cloud",
            api_key="test_key",
            api_secret="test_secret",
            webhook_base_url="https://abcd1234.ngrok-free.app",
        )
        provider = CloudinaryMediaProvider(config)

        signed = provider.generate_signed_upload("tru_connect/suppliers/x/products/y/z", 1600)

        assert signed.notification_url == "https://abcd1234.ngrok-free.app/api/v1/media/webhooks/cloudinary-scan"

    def test_omitted_from_signature_when_not_configured(self, provider, config):
        """Empty webhook_base_url -- the upload must still succeed and
        sign correctly; it just never requests a callback. Matches
        this whole build's own "stay honest about what isn't wired up
        yet" discipline rather than signing a broken/empty callback
        URL Cloudinary would reject outright."""
        signed = provider.generate_signed_upload("tru_connect/suppliers/x/products/y/z", 1600)

        assert signed.notification_url == ""

    def test_trailing_slash_on_webhook_base_url_is_stripped(self, monkeypatch):
        monkeypatch.setenv("CLOUDINARY_CLOUD_NAME", "test_cloud")
        monkeypatch.setenv("CLOUDINARY_API_KEY", "test_key")
        monkeypatch.setenv("CLOUDINARY_API_SECRET", "test_secret")
        monkeypatch.setenv("CLOUDINARY_WEBHOOK_BASE_URL", "https://abcd1234.ngrok-free.app/")

        config = MediaConfig.from_env()

        assert config.notification_url == "https://abcd1234.ngrok-free.app/api/v1/media/webhooks/cloudinary-scan"
