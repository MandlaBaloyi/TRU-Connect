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
        signed = provider.generate_signed_upload("tru_connect/suppliers/sup1/products/prod1/asset1", 1600, "tru_connect/suppliers/sup1/products/prod1")

        assert signed.cloud_name == config.cloud_name
        assert signed.api_key == config.api_key
        assert signed.public_id == "tru_connect/suppliers/sup1/products/prod1/asset1"
        assert signed.signature  # non-empty
        assert signed.timestamp > 0
        assert "jpg" in signed.allowed_formats

    def test_asset_folder_is_set_and_signed(self, provider):
        """THE REAL FIX found during Media Library review: public_id's
        own path and Cloudinary's separate asset_folder parameter look
        identical but are genuinely independent -- an upload could be
        fully find-able by search while never appearing in the
        browsable Folders tree at all. Confirms asset_folder is both
        echoed on the response AND baked into the actual signature
        (changing it must change the signature -- if it weren't part
        of what's signed, this codebase could silently drift from what
        Cloudinary actually receives)."""
        signed = provider.generate_signed_upload(
            "tru_connect/suppliers/sup1/products/prod1/asset1", 1600, "tru_connect/suppliers/sup1/products/prod1"
        )
        assert signed.asset_folder == "tru_connect/suppliers/sup1/products/prod1"

        signed_different_folder = provider.generate_signed_upload(
            "tru_connect/suppliers/sup1/products/prod1/asset1", 1600, "tru_connect/suppliers/sup1/products/prod2"
        )
        assert signed.signature != signed_different_folder.signature

    def test_api_secret_never_appears_in_the_signed_upload(self, provider, config):
        """The one property that matters most -- the secret must never
        leave this process."""
        signed = provider.generate_signed_upload("tru_connect/suppliers/sup1/products/prod1/asset1", 1600, "tru_connect/suppliers/sup1/products/prod1")

        serialized = str(signed)
        assert config.api_secret not in serialized

    def test_different_public_ids_produce_different_signatures(self, provider):
        first = provider.generate_signed_upload("tru_connect/suppliers/sup1/products/prod1/asset1", 1600, "tru_connect/suppliers/sup1/products/prod1")
        second = provider.generate_signed_upload("tru_connect/suppliers/sup1/products/prod2/asset2", 1600, "tru_connect/suppliers/sup1/products/prod2")

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

    def test_upload_notification_with_pending_moderation_array_is_ignored_not_error(self, provider):
        """THE REAL BUG, confirmed against real device-test evidence
        before this fix existed: Cloudinary's "upload" notification can
        ALSO carry its own moderation array with status: "pending" (a
        real payload example, not fabricated). That "pending" value
        used to flow straight into the unrecognised-status branch and
        get mapped to ERROR -- a false, terminal verdict written to the
        database SECONDS before the real "moderation" notification
        (the genuine approved/rejected result) arrives right behind it.
        Because apply_scan_result's own idempotency guard correctly
        refuses to overwrite an already-terminal status, that false
        ERROR permanently blocked the real result from ever landing.
        Must be IGNORED, unconditionally, regardless of where "pending"
        shows up in the payload."""
        real_upload_notification_with_pending_moderation = {
            "notification_type": "upload",
            "public_id": "tru_connect/suppliers/sup1/products/prod1/asset1",
            "moderation": [{"kind": "perception_point", "status": "pending"}],
        }

        result = provider.parse_scan_result(real_upload_notification_with_pending_moderation)

        assert result.status == "IGNORED"

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

        signed = provider.generate_signed_upload("tru_connect/suppliers/x/products/y/z", 1600, "tru_connect/suppliers/x/products/y")

        assert signed.notification_url == "https://abcd1234.ngrok-free.app/api/v1/media/webhooks/cloudinary-notifications"

    def test_omitted_from_signature_when_not_configured(self, provider, config):
        """Empty webhook_base_url -- the upload must still succeed and
        sign correctly; it just never requests a callback. Matches
        this whole build's own "stay honest about what isn't wired up
        yet" discipline rather than signing a broken/empty callback
        URL Cloudinary would reject outright."""
        signed = provider.generate_signed_upload("tru_connect/suppliers/x/products/y/z", 1600, "tru_connect/suppliers/x/products/y")

        assert signed.notification_url == ""

    def test_trailing_slash_on_webhook_base_url_is_stripped(self, monkeypatch):
        monkeypatch.setenv("CLOUDINARY_CLOUD_NAME", "test_cloud")
        monkeypatch.setenv("CLOUDINARY_API_KEY", "test_key")
        monkeypatch.setenv("CLOUDINARY_API_SECRET", "test_secret")
        monkeypatch.setenv("CLOUDINARY_WEBHOOK_BASE_URL", "https://abcd1234.ngrok-free.app/")

        config = MediaConfig.from_env()

        assert config.notification_url == "https://abcd1234.ngrok-free.app/api/v1/media/webhooks/cloudinary-notifications"


class TestUploadAssetTransformationFormat:
    """THE REAL BUG found during real device testing: every server-
    side bulk-import upload was failing with Cloudinary's own
    "Transformation Unknown transformation c_limit" error. Root cause,
    confirmed directly against the installed SDK's own source, not
    guessed: cloudinary.uploader.upload() feeds a `transformation`
    kwarg through utils.generate_transformation_string(), which
    treats a PLAIN STRING as the NAME of a saved, pre-registered
    transformation preset (visible as a "t_" prefix in its own
    output) -- NOT as inline parameter shorthand. Since no such preset
    was ever registered, every server-side upload failed. This never
    affected generate_signed_upload, which sends its own string
    straight to Cloudinary's raw HTTP endpoint -- a completely
    different, unaffected code path that parses that exact shorthand
    natively and correctly."""

    def test_string_form_is_the_documented_broken_shape(self):
        """Proves the bug exists, using the REAL installed SDK -- not
        an assumption about what it does."""
        from cloudinary.utils import generate_transformation_string

        result, _ = generate_transformation_string(transformation="c_limit,w_1600,h_1600,q_auto")

        # The "t_" prefix is Cloudinary's own named-transformation
        # lookup syntax -- exactly the wrong thing, and exactly what
        # produced the real "Unknown transformation c_limit" error.
        assert result.startswith("t_")

    def test_dict_form_produces_a_valid_inline_transformation(self):
        """Proves the fix -- the SDK's own documented correct input
        shape genuinely produces valid inline shorthand, not another
        named-transformation lookup."""
        from cloudinary.utils import generate_transformation_string

        result, _ = generate_transformation_string(
            transformation={"crop": "limit", "width": 1600, "height": 1600, "quality": "auto"}
        )

        assert not result.startswith("t_")
        assert "c_limit" in result
        assert "w_1600" in result
        assert "h_1600" in result
        assert "q_auto" in result

    def test_upload_asset_passes_the_dict_form_not_the_broken_string_form(self, monkeypatch):
        """Confirms upload_asset itself -- not just the two helper
        functions in isolation -- actually calls the SDK with the
        correct shape. Patches cloudinary.uploader.upload directly to
        capture exactly what this codebase sends it."""
        import cloudinary.uploader

        captured = {}

        def fake_upload(file_bytes, **kwargs):
            captured.update(kwargs)
            return {
                "public_id": kwargs["public_id"],
                "secure_url": "https://res.cloudinary.com/test/fake.jpg",
                "resource_type": "image",
                "format": "jpg",
                "width": 100,
                "height": 100,
                "bytes": len(file_bytes),
            }

        monkeypatch.setattr(cloudinary.uploader, "upload", fake_upload)

        config = MediaConfig(cloud_name="test_cloud", api_key="test_key", api_secret="test_secret")
        provider = CloudinaryMediaProvider(config)
        provider.upload_asset("tru_connect/suppliers/x/products/y/z", b"fake bytes", 1600, "tru_connect/suppliers/x/products/y")

        assert isinstance(captured["transformation"], dict)
        assert captured["transformation"] == {"crop": "limit", "width": 1600, "height": 1600, "quality": "auto"}


class TestModerationToggle:
    """The real fix that closed the loop on real device testing --
    installing the Perception Point add-on alone does NOT scan
    anything (confirmed directly against Cloudinary's own docs); every
    upload has to explicitly request it via this parameter."""

    def test_moderation_included_when_enabled(self, provider):
        signed = provider.generate_signed_upload("tru_connect/suppliers/x/products/y/z", 1600, "tru_connect/suppliers/x/products/y")

        assert signed.moderation == "perception_point"

    def test_moderation_omitted_when_disabled(self):
        config = MediaConfig(
            cloud_name="test_cloud", api_key="test_key", api_secret="test_secret", moderation_enabled=False
        )
        provider = CloudinaryMediaProvider(config)

        signed = provider.generate_signed_upload("tru_connect/suppliers/x/products/y/z", 1600, "tru_connect/suppliers/x/products/y")

        assert signed.moderation == ""

    def test_disabled_env_value_is_actually_read(self, monkeypatch):
        monkeypatch.setenv("CLOUDINARY_CLOUD_NAME", "test_cloud")
        monkeypatch.setenv("CLOUDINARY_API_KEY", "test_key")
        monkeypatch.setenv("CLOUDINARY_API_SECRET", "test_secret")
        monkeypatch.setenv("CLOUDINARY_MODERATION_ENABLED", "false")

        config = MediaConfig.from_env()

        assert config.moderation_enabled is False

    def test_is_moderation_enabled_reflects_the_config(self):
        enabled_provider = CloudinaryMediaProvider(
            MediaConfig(cloud_name="c", api_key="k", api_secret="s", moderation_enabled=True)
        )
        disabled_provider = CloudinaryMediaProvider(
            MediaConfig(cloud_name="c", api_key="k", api_secret="s", moderation_enabled=False)
        )

        assert enabled_provider.is_moderation_enabled() is True
        assert disabled_provider.is_moderation_enabled() is False
