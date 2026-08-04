"""
Receipt MECHANICS -- never receipt CONTENT.

THE SPLIT, AND WHY IT MATTERS:
    This package knows how to make a receipt SECURE and VERIFIABLE:
    reference numbers, QR payloads, signatures, verification hashes.

    It must NEVER know what a receipt SAYS. It does not know the words
    "Loan Book", "Wallet", "Supplier", "invoice", or "customer". It has
    no idea a credit sale exists.

    Each domain owns its own receipt CONTENT -- Loan Book decides the
    title, customer name, disclaimer and footer; Wallet decides the
    payment-confirmation wording; Supplier Payments decides invoice and
    VAT lines. All three call the SAME mechanics here.

    Exactly the same shape as email templates: one sending engine, many
    domain-owned templates.

CURRENT STATUS -- deliberately minimal:
    reference.py is real and in use (Loan Book's frontend already
    generates LB-XXXXXX references today).

    qr.py, signing.py and verification.py are NOT implemented, on
    purpose. Real signing needs a server-held private key -- which the
    backend work now makes possible -- but building it before there is a
    real key, a real verification endpoint, and a real threat model
    would produce something that LOOKS verified without BEING verified,
    which is worse than no signature at all.
"""
