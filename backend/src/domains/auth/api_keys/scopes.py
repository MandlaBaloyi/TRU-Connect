"""
The scope vocabulary for API keys.

A CLOSED SET, DEFINED BY US. Scopes are not free text a supplier types:
an unknown scope on a key is worse than no scope, because it looks like
permission and grants nothing, and the failure surfaces months later as
"the integration stopped working" rather than as a validation error at
the moment the mistake was made.

WHY SCOPES AT ALL, GIVEN EVERY KEY BELONGS TO ONE SUPPLIER AND CAN ONLY
EVER TOUCH THAT SUPPLIER'S OWN DATA. Because the blast radius of a
leaked key is decided here. An ERP that pushes a price file needs
CATALOGUE_WRITE and nothing else; a key that leaks from that server
should not also be able to read the order book, which contains the names
and addresses of every business buying from them. "It is all their own
data anyway" is exactly the reasoning that turns one leaked credential
into a full account dump.

DELIBERATELY SMALL. Four scopes, each mapping to something that exists
today. The temptation is to pre-declare a dozen for surfaces not built
yet -- but a scope nothing enforces is a promise the API is not keeping,
and suppliers will grant it, and one day it will start meaning something
without anyone re-consenting. Add a scope in the same commit as the
endpoint that checks it.
"""
from __future__ import annotations

# Read the supplier's own products and offers as we hold them -- what
# their system reconciles against after a push.
CATALOGUE_READ = "catalogue:read"

# Create and update their products, prices, and stock. The one the
# integration path in V2 2.4 actually needs.
CATALOGUE_WRITE = "catalogue:write"

# Read orders placed with them. Kept separate from catalogue on purpose:
# this is the scope that carries other people's business names, delivery
# addresses and buying patterns, and it should be possible to run a
# price-push integration without ever granting it.
ORDERS_READ = "orders:read"

# Acknowledge, fulfil, or decline orders from their own system.
ORDERS_WRITE = "orders:write"

ALL_SCOPES = frozenset(
    {
        CATALOGUE_READ,
        CATALOGUE_WRITE,
        ORDERS_READ,
        ORDERS_WRITE,
    }
)

# What the portal offers when someone creates a key, in the order it
# should be shown -- read before write, catalogue before orders, so the
# least dangerous option is the first one the eye lands on.
SCOPE_CHOICES = (CATALOGUE_READ, CATALOGUE_WRITE, ORDERS_READ, ORDERS_WRITE)

SCOPE_DESCRIPTIONS = {
    CATALOGUE_READ: "Read your products, prices and stock levels.",
    CATALOGUE_WRITE: "Create and update your products, prices and stock levels.",
    ORDERS_READ: "Read orders placed with you, including the buying business's details.",
    ORDERS_WRITE: "Accept, decline and update the status of orders.",
}


def unknown_scopes(scopes) -> list:
    """Returns the scopes that are not in the vocabulary, so the caller
    can name them all at once rather than rejecting one per attempt."""
    return sorted(set(scopes) - ALL_SCOPES)
