"""
Manual verification script -- NOT part of the app, never imported by
anything in src/. Run this ONCE, locally, after you've put your real
CLOUDINARY_API_SECRET in .env, to prove the exact signing logic this
backend uses actually works against real Cloudinary -- not a fake
provider standing in for it (see shared/media/cloudinary_provider.py's
own docstring on why the automated test suite can't do this itself:
this sandbox has no network access to api.cloudinary.com).

Usage:
    cd backend
    python scripts/verify_cloudinary_connection.py

Uploads one real, tiny test image using the SAME signing code path as
CloudinaryMediaProvider.generate_signed_upload (calls it directly, not
a reimplementation), then confirms Cloudinary actually accepted it and
the response looks like what product_media_service.register_uploaded_media
expects to receive from the client. Deletes the test asset afterward
so it doesn't sit in your account.
"""
from __future__ import annotations

import os
import sys
import uuid

from dotenv import load_dotenv

load_dotenv()

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared.media.providers.cloudinary_provider import CloudinaryMediaProvider
from src.shared.media.config.media_config import MediaConfig

# A tiny, real 1x1 red pixel PNG -- doesn't need an external file.
TEST_IMAGE_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108020000009077"
    "53de0000000c4944415408d763f8cfc0c0c00003030001ac37a20d0000000049454e44ae426082"
)


def main() -> int:
    config = MediaConfig.from_env()

    if not config.cloud_name or not config.api_key or not config.api_secret:
        print("Missing CLOUDINARY_CLOUD_NAME / CLOUDINARY_API_KEY / CLOUDINARY_API_SECRET in .env")
        return 1
    if config.api_secret.startswith("REPLACE_WITH"):
        print("CLOUDINARY_API_SECRET is still the placeholder value -- put your real secret in .env first.")
        return 1

    provider = CloudinaryMediaProvider(config)
    public_id = f"tru_connect/_verify/{uuid.uuid4()}"

    print(f"Requesting a signed upload for: {public_id}")
    # 1600px matches products/tiers/*.py's own stored_max_dimension_px
    # default -- this script exercises the exact same ingest-time
    # compression every real product photo upload will use.
    signed = provider.generate_signed_upload(public_id, max_dimension_px=1600)
    print(f"  signature: {signed.signature[:12]}... (truncated)")
    print(f"  upload_url: {signed.upload_url}")

    print("Uploading a real test image directly to Cloudinary (bypassing this backend, as designed)...")
    response = requests.post(
        signed.upload_url,
        data={
            "api_key": signed.api_key,
            "timestamp": signed.timestamp,
            "signature": signed.signature,
            "public_id": signed.public_id,
            "allowed_formats": signed.allowed_formats,
            "transformation": signed.transformation,
        },
        files={"file": ("test.png", TEST_IMAGE_BYTES, "image/png")},
        timeout=30,
    )

    if response.status_code != 200:
        print(f"UPLOAD FAILED -- status {response.status_code}")
        print(response.text)
        return 1

    result = response.json()
    print("Upload succeeded. Cloudinary returned:")
    print(f"  public_id:  {result.get('public_id')}")
    print(f"  secure_url: {result.get('secure_url')}")
    print(f"  format:     {result.get('format')}")
    print(f"  bytes:      {result.get('bytes')}")

    if result.get("public_id") != public_id:
        print("WARNING: returned public_id doesn't match what was requested.")

    print("Cleaning up (deleting the test asset)...")
    provider.delete_asset(public_id)
    print("Done. The real signing flow works end-to-end against your Cloudinary account.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
