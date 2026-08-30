"""
PaymentConfig -- NOT wired to anything yet. Kept as a real, correctly-
shaped scaffold (matching shared/media/config/media_config.py's own
"only what's genuinely universal, nothing here is a business rule"
discipline) so payfast_provider.py has a real config object to read
from the moment it's actually implemented, rather than that work
starting from a blank file too.

WHAT WILL LIVE HERE, based on confirmed research (see
providers/payfast_provider.py's own module docstring for the sources):
- TRU Connect's OWN PayFast Merchant ID/Key -- TRU Connect is the
  SECONDARY (receiving) party in every split, per PayFast's own model,
  so this is genuinely one, single, platform-wide credential, not
  per-supplier. Per-supplier credentials (the PRIMARY side of each
  split) live on SupplierProfile itself, not here -- same reasoning
  MediaConfig already used to justify why photo-count limits don't
  live in that file either: a supplier-specific value isn't a
  genuinely universal payment-provider setting.
- A passphrase (PayFast signs/validates requests with one).
- sandbox vs live mode -- a real, explicit toggle, same "never
  hardcoded, always an env var" discipline as MediaConfig's own
  moderation_enabled.
- The public webhook base URL PayFast's own ITN calls back to --
  genuinely absent (empty string) until a real tunnel/domain is
  configured, exactly like MediaConfig.webhook_base_url already
  defaults to "" rather than a broken guessed value.

NONE OF THIS IS READ BY ANYTHING YET. ManualPaymentProvider (what
actually runs today) never imports this file at all -- see
providers/composition.py's own docstring for how that isolation is
actually enforced, not just conventionally true.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentConfig:
    merchant_id: str
    merchant_key: str
    passphrase: str
    sandbox_mode: bool = True
    webhook_base_url: str = ""

    @classmethod
    def from_env(cls) -> "PaymentConfig":
        return cls(
            merchant_id=os.environ.get("PAYFAST_MERCHANT_ID", ""),
            merchant_key=os.environ.get("PAYFAST_MERCHANT_KEY", ""),
            passphrase=os.environ.get("PAYFAST_PASSPHRASE", ""),
            sandbox_mode=os.environ.get("PAYFAST_SANDBOX_MODE", "true").lower() != "false",
            webhook_base_url=os.environ.get("PAYFAST_WEBHOOK_BASE_URL", "").rstrip("/"),
        )
