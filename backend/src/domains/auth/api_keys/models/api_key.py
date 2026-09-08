"""
API Key Model (V2 2.10) -- the machine door.

WHAT THIS IS FOR
----------------
A medium-to-large supplier does not sit in a portal typing prices. Their
ERP or warehouse system pushes a catalogue at us on a schedule, with no
human present. That caller cannot log in: there is no password to type,
no OTP inbox to check, no browser to hold a cookie. It needs a
credential a machine can hold, and this is that credential.

It is also, per V2 2.10, explicitly NOT an OAuth2 authorization-code +
PKCE flow. PKCE exists for PUBLIC clients that cannot keep a secret --
mobile apps and browser SPAs. A supplier's ERP server CAN keep a secret,
which is why every platform that actually has this problem (Stripe,
Shopify, Takealot) hands out scoped API keys rather than running an
identity-provider dance against itself.

WHAT IS STORED, AND WHAT IS NOT
--------------------------------
The key itself is never stored, anywhere, in any form we can reverse.
Three columns carry what is needed:

  prefix    the public half. Printed in the portal list so a supplier
            can tell "the one on the Joburg server" from "the one Sam
            made in March". Identifies a key; cannot be used as one.
  key_hash  SHA-256 of the whole secret. This is what a presented key
            is checked against.
  name      what the supplier called it.

The full key exists exactly once, in the response to the call that
created it. If they lose it they make another -- there is no "show me
the key again" and there must never be one, because the moment such an
endpoint exists, every path that can read the database can read live
credentials.

WHY SHA-256 AND NOT BCRYPT, WHICH IS USED FOR PASSWORDS
--------------------------------------------------------
This looks like an inconsistency with shared/security/security.py and is
not. bcrypt is deliberately SLOW, because a human password is short,
guessable, and frequently reused -- the cost is what makes an offline
crack of a leaked table impractical.

An API key here is 32 characters from a CSPRNG. There is no dictionary
to run against it and no human pattern to exploit; brute force is
infeasible against a fast hash and an infeasible-squared against a slow
one. What a slow hash WOULD buy is a per-request bcrypt on an endpoint
designed to be hammered by an automated integration -- a self-inflicted
denial of service, paid for on every legitimate call, in exchange for
security we already have from the entropy. Every platform named above
made the same call for the same reason.

REVOCATION IS A COLUMN, NOT A DELETE
-------------------------------------
revoked_at rather than a row removal, because "this key was used to
change your prices on the 3rd, and was turned off on the 5th" is a
question someone will eventually need answered -- and a deleted row
cannot answer it. Same reasoning as RefreshToken.

Soft-delete from BaseModel is deliberately NOT the revocation mechanism:
is_deleted means "this record is gone from the product's point of view",
revoked_at means "this credential no longer authenticates". They are
different facts and collapsing them would make an accidental
soft-delete-restore silently reactivate a killed credential.
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import ARRAY, UUID

from src.core.base_model import BaseModel, utcnow
from src.extensions import db


class ApiKey(BaseModel):
    __tablename__ = "api_keys"
    __table_args__ = {"schema": "auth"}

    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # What the supplier called it, e.g. "Warehouse sync (Pretoria)".
    # Required, because a list of four keys called nothing is a list
    # nobody dares revoke anything from.
    name = db.Column(db.String(80), nullable=False)

    # The public half, e.g. "tck_9f3a2b71". Unique and indexed because
    # authentication looks the key up by this, then compares hashes --
    # see ApiKeyRepository.get_by_prefix on why lookup is not done on
    # the hash directly.
    prefix = db.Column(db.String(32), unique=True, nullable=False, index=True)

    # SHA-256 hex of the full presented key. 64 chars, always.
    key_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # Postgres text[]. An array rather than a join table because scopes
    # are a short, fixed vocabulary owned by us (see scopes.py), not
    # user-created rows -- and every read wants all of them at once.
    scopes = db.Column(ARRAY(db.String(40)), nullable=False, default=list)

    # NULL until the key is first used. That NULL is itself the useful
    # signal: a key created three months ago that has never been used is
    # a key somebody generated, pasted into a config, and got wrong --
    # or never deployed at all.
    last_used_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Optional. A key with no expiry is the normal case for a running
    # integration; a dated one is for the contractor who is setting it
    # up and should not still have access in June.
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)

    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def is_active(self) -> bool:
        """True only if this key may authenticate right now.

        Checks all three ways a key can be dead -- revoked, expired,
        soft-deleted -- in ONE place, so no caller can authenticate
        against a key by remembering two of the three.
        """
        if self.is_deleted or self.revoked_at is not None:
            return False
        if self.expires_at is not None and self.expires_at <= utcnow():
            return False
        return True

    def has_scopes(self, required) -> bool:
        granted = set(self.scopes or [])
        return set(required).issubset(granted)

    def to_public_dict(self) -> dict:
        """Everything the portal shows about a key. NO SECRET, by
        construction -- there is no column here that could leak one."""
        return {
            "id": str(self.id),
            "name": self.name,
            "prefix": self.prefix,
            "scopes": sorted(self.scopes or []),
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "lastUsedAt": self.last_used_at.isoformat() if self.last_used_at else None,
            "expiresAt": self.expires_at.isoformat() if self.expires_at else None,
            "revokedAt": self.revoked_at.isoformat() if self.revoked_at else None,
            "active": self.is_active(),
        }
