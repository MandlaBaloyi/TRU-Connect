"""
Authorization decorators.
 (role_required,
permission_required ),
Objective 3 (login_required, verified_required, active_account_required,
fully_authenticated -- NEW).

verified_required / active_account_required / fully_authenticated
deliberately RE-CHECK THE DATABASE on every request rather than trusting
a JWT claim. A claim baked into a token at issue time cannot reflect a
status that changes afterwards (e.g. an account verified, or
deactivated, after its current token was already issued) without an
explicit token re-issue -- a database check is what actually closes
that gap, at the cost of one extra query per protected request.
"""
from __future__ import annotations

from functools import wraps

from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from src.core.exceptions import AccountInactiveError, EmailNotVerifiedError, ForbiddenError


def _load_current_user():
    """Local import avoids a circular import between core (imported very
    early, by the app factory) and the auth domain."""
    from src.domains.auth.repositories.user_repository import UserRepository

    return UserRepository.get_by_id(get_jwt_identity())


# How stale last_active_at is allowed to get before a request bothers
# writing it.
#
# ONE MINUTE, because the display is minute-accurate: a business about
# to place an order is asking "will someone see this in the next few
# minutes", and "Active 5 minutes ago" vs "Active now" are different
# answers. A coarser throttle would make the app report someone as
# absent while they were actively using it -- the reading can never be
# fresher than the write. Still bounded: one row update per minute per
# ACTIVE user, not one per request.
LAST_ACTIVE_THROTTLE_MINUTES = 1

#: Roles that BUY or SELL on the platform, as opposed to operating it.
#: Staff accounts are deliberately absent -- see participants_only.
PARTICIPANT_ROLES = ("business", "supplier")


def _touch_last_active(user) -> None:
    """Record that this user is using the app, at most once every
    LAST_ACTIVE_THROTTLE_MINUTES.

    NEVER RAISES. This is a side effect on the way to someone's actual
    request -- a failed heartbeat write must not turn a working page
    into an error. On failure it rolls back just this write, so the
    session is left clean for the route that's about to run.

    Recorded for every role. Whether anyone else ever SEES it is a
    separate, opt-in decision (SupplierProfile.show_last_active).
    """
    from datetime import timedelta

    from src.core.base_model import utcnow
    from src.extensions import db

    try:
        now = utcnow()
        if user.last_active_at is not None and now - user.last_active_at < timedelta(
            minutes=LAST_ACTIVE_THROTTLE_MINUTES
        ):
            return
        user.last_active_at = now
        db.session.commit()
    except Exception:  # noqa: BLE001
        try:
            db.session.rollback()
        except Exception:  # noqa: BLE001
            pass


def login_required(fn):
    """Thin, explicitly-named wrapper around flask_jwt_extended's
    jwt_required() -- exists so route declarations read @login_required
    rather than a raw library call, and so future session/audit hooks
    have one place to attach to."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


def verified_required(fn):
    """Requires authentication AND a current, database-fresh
    verification_status == VERIFIED. This is the decorator that closes
    the "a valid token from an unverified account can still be used"
    hole -- apply it to any endpoint an unverified user must not reach."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        from src.domains.auth.models.user import VerificationStatus

        user = _load_current_user()
        if user is None or user.verification_status != VerificationStatus.VERIFIED:
            raise EmailNotVerifiedError("Please verify your email before continuing.")
        return fn(*args, **kwargs)

    return wrapper


def active_account_required(fn):
    """Requires authentication and account_status == ACTIVE."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        from src.domains.auth.models.user import AccountStatus

        user = _load_current_user()
        if user is None or user.account_status != AccountStatus.ACTIVE:
            raise AccountInactiveError("This account is not active.")
        return fn(*args, **kwargs)

    return wrapper


def fully_authenticated(fn):
    """Convenience combination: authenticated + verified + active, in
    ONE decorator and ONE database lookup, for the common case (Auth
    Hardening, Objective 3 examples: /dashboard, /orders,
    /profile, /catalogue, /notifications)."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        from src.domains.auth.models.user import AccountStatus, VerificationStatus

        user = _load_current_user()
        if user is None or user.verification_status != VerificationStatus.VERIFIED:
            raise EmailNotVerifiedError("Please verify your email before continuing.")
        if user.account_status != AccountStatus.ACTIVE:
            raise AccountInactiveError("This account is not active.")
        # The one hook every real in-app screen already passes through,
        # with the user row ALREADY loaded -- so the heartbeat costs a
        # throttled write and no extra query. Deliberately not on
        # login_required (which never loads the user) or on the
        # single-check decorators, which guard narrower paths.
        _touch_last_active(user)
        return fn(*args, **kwargs)

    return wrapper


def role_required(*allowed_roles: str):
    """
    Stacks JWT verification + role authorization in one decorator.
    Supports every role in UserRole and any future role added to that
    enum without this decorator changing."""

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") not in allowed_roles:
                raise ForbiddenError("You do not have permission to access this resource.")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def participants_only(fn):
    """Business or supplier -- somebody who BUYS or SELLS on TruConnect.

    WHAT THIS IS FOR, and it is not a synonym for "logged in". Fifty
    authenticated endpoints pin no role at all, because for a long time
    there were only two roles and "authenticated" and "is a participant"
    were the same sentence. They stop being the same sentence the moment
    a STAFF account can hold a token.

    The endpoints in question are the Loan Book, the Order Book, the
    business profile, notifications and the two shared connections
    routes. None of them belong to a staff account: an admin has no
    customers who owe them money, no suppliers, and no shopfront.

    THE CONCRETE HARM THIS PREVENTS. Several of those routes branch on
    the caller's role, and at least one of them WROTE: photo settings
    did `if supplier ... else <business>`, so a staff token reaching it
    would have created a business profile row and quietly made an admin
    into a marketplace participant. Those branches are now exhaustive
    (they raise on an unknown role), and this decorator is the second
    layer -- refusing at the door rather than three calls deep, so the
    failure is a clear 403 instead of an exception from a service that
    was never meant to see this caller.

    WHY NOT role_required("business", "supplier"). It would behave the
    same today and say something different: that list is a coincidence
    of which roles happen to exist. This name states the RULE -- staff
    are not participants -- so when a fourth role arrives, whoever adds
    it can tell at a glance which side of the line it belongs on.
    """

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if get_jwt().get("role") not in PARTICIPANT_ROLES:
            raise ForbiddenError("This is only available to business and supplier accounts.")
        return fn(*args, **kwargs)

    return wrapper


def api_key_required(*required_scopes: str):
    """Authenticates a MACHINE caller by API key (V2 2.10).

    THE THIRD AUTHENTICATION MECHANISM, alongside the mobile app's
    bearer JWT and the web portal's cookie. It exists because a
    supplier's ERP has no human: nobody to type a password, read an OTP,
    or hold a session. It pushes a catalogue at 03:00 and needs a
    credential a server can hold.

    DELIBERATELY NOT STACKED WITH @jwt_required. A request authenticated
    by key has no JWT at all, so get_jwt_identity() is empty on these
    routes -- read the caller from `g.api_key_user_id` instead. Mixing
    the two would produce an endpoint where a missing key silently falls
    back to a session, which is the kind of "convenience" that turns
    into an authentication bypass.

    THE SCOPE CHECK IS PART OF THE DECORATOR, not a separate one to
    remember. An endpoint that authenticates a key without also
    declaring what the key must be allowed to do is an endpoint every
    key can reach, and that mistake is invisible in review -- the route
    looks protected.

    Sets on `g`:
        g.api_key          the ApiKey record
        g.api_key_user_id  the owning supplier's id (str)
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask import g, request

            from src.domains.auth.api_keys.services.api_key_service import ApiKeyService
            from src.domains.auth.models.user import AccountStatus

            # Authorization: Bearer <key>, the same header shape every
            # integration developer already expects, distinguished from
            # a JWT by the key's own "tck_" prefix rather than by a
            # bespoke header nobody would guess.
            header = request.headers.get("Authorization", "")
            raw_key = header[7:].strip() if header.startswith("Bearer ") else None

            key = ApiKeyService.authenticate(raw_key, ip_address=request.remote_addr)
            ApiKeyService.require_scopes(key, required_scopes)

            # The KEY being valid is not the same as the ACCOUNT being
            # usable. A supplier deactivated this morning still holds
            # keys minted last year, and those must stop working the
            # moment the account does -- the same database-fresh check
            # the human decorators make, for the same reason.
            from src.domains.auth.repositories.user_repository import UserRepository

            owner = UserRepository.get_by_id(key.user_id)
            if owner is None or owner.account_status != AccountStatus.ACTIVE:
                raise AccountInactiveError("This account is not active.")

            g.api_key = key
            g.api_key_user_id = str(key.user_id)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def idempotent(fn):
    """Make a POST safe to retry (V2_13 §3.1).

    OPT-IN PER REQUEST, not per endpoint. A caller that sends no
    Idempotency-Key header gets exactly today's behaviour -- so adding
    this decorator to a live route changes nothing for the mobile app
    and everything for a machine that chooses to use it. That is the
    property which lets it be applied broadly without a migration of
    client behaviour.

    THE HEADER IS THE CLIENT'S TO GENERATE, and that is not laziness on
    our part: only the client knows which two requests are "the same
    one, sent twice". A server-generated key would be a different key
    on the retry and would protect nothing.

    WHAT A RETRY GETS:
        the SAME status code and the SAME body, replayed from storage,
        without the handler running again.

    AND WHAT A MISUSED KEY GETS:
        409  another copy of this request is still in flight
        422  this key was already used for a DIFFERENT body

    The second is a client bug, and returning the first response would
    hide it -- the caller would believe a request they never really
    made had succeeded.

    Stacks UNDER the auth decorators, because the key is scoped to the
    caller and there is no caller until authentication has run.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask import jsonify, request

        from src.shared.idempotency import service as idempotency

        key = (request.headers.get("Idempotency-Key") or "").strip()
        if not key:
            return fn(*args, **kwargs)

        try:
            user_id = get_jwt_identity()
        except Exception:  # noqa: BLE001 -- an api-key caller has no JWT
            user_id = None
        if user_id is None:
            from flask import g

            user_id = getattr(g, "api_key_user_id", None)

        request_hash = idempotency.fingerprint(request.get_data() or b"")
        endpoint = f"{request.method} {request.path}"

        try:
            row = idempotency.claim(key, user_id, endpoint, request_hash)
        except idempotency.IdempotencyInFlight as exc:
            return jsonify({"success": False, "message": str(exc), "errors": []}), 409
        except idempotency.IdempotencyConflict as exc:
            return jsonify({"success": False, "message": str(exc), "errors": []}), 422

        if row.is_complete:
            # THE REPLAY. The handler does not run at all.
            return jsonify(row.response_body), row.status_code

        try:
            response = fn(*args, **kwargs)
        except Exception:
            # RELEASED, NOT STORED. The handler raised, so its
            # transaction rolled back and there is nothing to protect
            # against -- while a stored 500 would make the client's
            # only recovery inventing a new key, which is how
            # duplicates get made.
            idempotency.release(row)
            raise

        body, status = _unwrap(response)
        if status >= 500:
            idempotency.release(row)
        else:
            idempotency.complete(row, status, body)
        return response

    return wrapper


def _unwrap(response):
    """(json body, status code) from whatever a route returned.

    Flask routes here return either `jsonify(...)` or the
    `(response, status)` tuple that success_response/error_response
    produce, so both shapes have to be understood -- and a route that
    returned something else entirely should not be silently stored as
    if it were JSON.
    """
    status = 200
    payload = response
    if isinstance(response, tuple):
        payload = response[0]
        if len(response) > 1 and isinstance(response[1], int):
            status = response[1]
    body = None
    if hasattr(payload, "get_json"):
        try:
            body = payload.get_json(silent=True)
        except Exception:  # noqa: BLE001
            body = None
        if getattr(payload, "status_code", None):
            status = payload.status_code if not isinstance(response, tuple) else status
    return body, status


def permission_required(*required_permissions: str):
    """UNCHANGED -- structural placeholder for granular permissions;
     for the full rationale."""

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            granted = set(claims.get("permissions", []))
            if not set(required_permissions).issubset(granted):
                raise ForbiddenError("You do not have permission to access this resource.")
            return fn(*args, **kwargs)

        return wrapper

    return decorator
