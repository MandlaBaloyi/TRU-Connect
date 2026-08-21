"""
Manual webhook-signature diagnostic -- NOT part of the app, never
imported by anything in src/. Run this ONCE, locally, to determine
FOR CERTAIN whether a 401 on the webhook is caused by:

  (a) Cloudinary signing with a DIFFERENT API key/secret than the one
      in your .env (the "multiple API keys" scenario Cloudinary's own
      docs warn about), or
  (b) something in our own request-handling code.

HOW TO GET THE THREE VALUES BELOW, from ngrok's inspector
(http://127.0.0.1:4040), on the SAME failed request:
  1. RAW_BODY    -- click the "Raw" tab, copy the EXACT body shown
                    (not the pretty-printed "Summary" view -- the
                    signature is computed over the exact original
                    bytes, so it must be copied byte-for-byte).
  2. TIMESTAMP    -- from the "Headers" tab, X-Cld-Timestamp value.
  3. EXPECTED_SIGNATURE -- from the "Headers" tab, X-Cld-Signature
                    value (the SHA1 one, NOT X-Cld-Signature-V2).

Usage:
    cd backend
    python scripts/diagnose_webhook_signature.py

If the computed signature MATCHES EXPECTED_SIGNATURE: your real
secret is correct, and the bug is in how our own code reads the
request -- tell me that result and I'll look at the route/verification
code directly, not guess further.

If it does NOT match: Cloudinary genuinely signed this with a secret
that isn't the one in your .env -- almost certainly the multiple-API-
keys scenario. The fix is telling our config which key to use, not a
bug in our verification logic.
"""
from __future__ import annotations

import hashlib
import os

from dotenv import load_dotenv

load_dotenv()

# --- Paste the three real values from ngrok's inspector here ---

RAW_BODY = """PASTE_THE_EXACT_RAW_BODY_HERE"""

TIMESTAMP = "PASTE_TIMESTAMP_HERE"

EXPECTED_SIGNATURE = "PASTE_X_CLD_SIGNATURE_HERE"

# -----------------------------------------------------------------


def main() -> int:
    api_secret = os.environ.get("CLOUDINARY_API_SECRET", "")
    if not api_secret or api_secret.startswith("REPLACE_WITH"):
        print("CLOUDINARY_API_SECRET isn't set in .env -- can't run this check.")
        return 1
    if "PASTE_" in RAW_BODY or "PASTE_" in TIMESTAMP or "PASTE_" in EXPECTED_SIGNATURE:
        print("Fill in RAW_BODY, TIMESTAMP, and EXPECTED_SIGNATURE from the ngrok inspector first.")
        return 1

    # This is the EXACT string Cloudinary's own SDK signs internally
    # (confirmed against the installed SDK's own source in an earlier
    # session): SHA1(body + timestamp + api_secret).
    to_sign = f"{RAW_BODY}{TIMESTAMP}{api_secret}"
    computed_signature = hashlib.sha1(to_sign.encode("utf-8")).hexdigest()

    print(f"Computed signature:  {computed_signature}")
    print(f"Cloudinary sent:     {EXPECTED_SIGNATURE}")
    print()

    if computed_signature == EXPECTED_SIGNATURE:
        print("MATCH -- your real secret is correct. The bug is in how our")
        print("own route reads the request, not the secret. Report this back.")
        return 0
    else:
        print("NO MATCH -- Cloudinary signed this with a different secret than")
        print("the one in your .env. Check Cloudinary Console -> Settings ->")
        print("API Keys for a second key, and use ITS secret for verification.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
