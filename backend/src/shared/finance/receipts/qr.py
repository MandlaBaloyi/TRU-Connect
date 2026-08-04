"""
QR payload construction -- NOT IMPLEMENTED, deliberately.

The payload shape depends on a verification endpoint that does not exist yet; guessing at that contract now means changing it after receipts carrying the old format are already circulating on people's phones.

WHY EMPTY RATHER THAN "BASIC": a signature that can be forged is worse
than no signature, because it invites people to TRUST a document that
hasn't actually been verified. Until real key management exists, Loan
Book's receipts carry a plain reference code and make no authenticity
claim anywhere in their wording. That is honest; a "Verified" badge
would not be.

NOTE for whoever implements this: even a perfect signature doesn't stop
someone photo-editing the visible amount on a shared image while leaving
a valid QR pointing elsewhere. Whoever verifies must be trained to trust
the SCANNED result, never the printed text.
"""

from __future__ import annotations


def _not_implemented(*args, **kwargs):  # noqa: ANN002, ANN003
    raise NotImplementedError(
        "QR payload construction is not implemented -- see this module's docstring."
    )
