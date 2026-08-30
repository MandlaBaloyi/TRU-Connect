"""
connections service-layer exceptions -- all real src.core.exceptions.
AppError subclasses, not a bespoke hierarchy. This deliberately follows
auth's convention (raise, let the app-wide error handler in src/__init__.py
convert it automatically), not loan_book's (a plain-Exception hierarchy
manually caught per-route) -- auth's own routes.py comment ("their own
try/except for those" -- meaning AppError subclasses need none) shows
this is already the cleaner, DRY pattern available in this exact
codebase; new code follows it rather than repeating loan_book's
per-route boilerplate.

SupplierNotFoundError, like auth's EmailNotVerifiedError, carries a
stable `code` the frontend can switch on. It's used for BOTH "genuinely
doesn't exist" and "exists but the search query didn't match it" --
there's no path in this domain where those two cases need to be told
apart in the response, so they aren't.
"""
from __future__ import annotations

from src.core.exceptions import ConflictError, NotFoundError, ValidationError


class SupplierNotFoundError(NotFoundError):
    code = "SUPPLIER_NOT_FOUND"


class BusinessNotFoundError(NotFoundError):
    """Mirrors SupplierNotFoundError exactly, for Find Business (the
    supplier-side search direction)."""

    code = "BUSINESS_NOT_FOUND"


class ConnectionRequestNotFoundError(NotFoundError):
    """Used for BOTH 'genuinely doesn't exist' and 'exists but belongs
    to a different supplier' -- same IDOR-safety reasoning as
    SupplierNotFoundError and loan_book's own LoanBookNotFoundError."""

    code = "REQUEST_NOT_FOUND"


class ProductNotFoundError(NotFoundError):
    """For get_supplier_product -- used for 'genuinely doesn't exist',
    'exists but belongs to a different supplier than the one in the
    URL', AND 'exists but is archived' all alike, same IDOR-safety
    reasoning as SupplierNotFoundError above: a business browsing a
    supplier's catalogue should never be able to tell an archived
    product apart from one that never existed."""

    code = "PRODUCT_NOT_FOUND"


class InvalidSearchQueryError(ValidationError):
    code = "INVALID_SEARCH_QUERY"


class InvalidCatalogQueryError(ValidationError):
    """Raised for an invalid page/limit/sort/category on
    list_supplier_products -- a genuinely different validation concern
    from InvalidSearchQueryError above (pagination/sort parameters, not
    a search string), kept as its own class rather than reused."""

    code = "INVALID_CATALOG_QUERY"


class ConnectionAlreadyRequestedError(ConflictError):
    """Raised only for a genuine attempted duplicate the idempotent
    request-connection path didn't already absorb -- see
    connections_service.py's own docstring on why the normal
    double-tap case returns the existing status instead of raising
    this."""

    code = "CONNECTION_ALREADY_REQUESTED"


class RetryLimitExceededError(ConflictError):
    """Raised when a retry-after-decline would exceed the daily or
    weekly cap (constants.MAX_CONNECTION_RETRY_PER_DAY/_PER_WEEK).
    Carries `data` with exactly when the next retry becomes allowed,
    so the frontend can show a real countdown rather than a bare
    'try again later'."""

    code = "RETRY_LIMIT_EXCEEDED"


class ConnectionNotActiveError(ConflictError):
    """Raised when trying to end a connection that exists but isn't
    currently ACTIVE (already ended, still pending, or was declined) --
    a genuine state conflict, not a "doesn't exist" case, so this uses
    ConflictError (409) rather than reusing
    ConnectionRequestNotFoundError."""

    code = "CONNECTION_NOT_ACTIVE"
