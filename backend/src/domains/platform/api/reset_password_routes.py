"""
Password Reset -- Browser Fallback Page.


Deliberately NOT under /api/v1 -- this must match the exact URL emailed
to the user: {APP_BASE_URL}/reset-password?ticket=...

Permanent, production web fallback for password reset -- reuses the
JSON API's exact backend logic (PasswordResetService, ResetPasswordSchema),
so validation rules and business behaviour can never drift between the
two entry points.

SECURITY NOTES
--------------
No CSRF token: this endpoint has no session/cookie-based ambient
credential to protect. The ticket itself -- unpredictable, single-use,
expiring -- IS the credential, submitted explicitly as a form field,
never auto-attached by the browser the way a cookie would be. An
attacker who already possesses a valid ticket gains nothing from a
forged cross-site request that a direct POST wouldn't already give
them.

IP rate limiting (via src.shared.cache.cache.check_rate_limit, the same
abstraction every other rate limit in this codebase uses) is defense-in-
depth, not the primary protection -- the ticket's entropy already makes
brute-forcing infeasible.

HTTPS IS REQUIRED IN PRODUCTION. Passwords transit in the POST body;
this file does not enforce HTTPS itself (doing so would break local
development) -- enforce it at the reverse proxy / load balancer.
"""
from __future__ import annotations

from flask import Blueprint, render_template, request
from marshmallow import ValidationError as MarshmallowValidationError

from src.core.exceptions import TicketInvalidError
from src.domains.auth.schemas.password_reset_schemas import ResetPasswordSchema
from src.domains.auth.services.password_reset_service import PasswordResetService
from src.shared.cache.cache import check_rate_limit

reset_password_bp = Blueprint("reset_password", __name__, template_folder="templates")

_reset_password_schema = ResetPasswordSchema()

WEB_RESET_MAX_ATTEMPTS_PER_HOUR = 30


def _flatten_errors(messages) -> list:
    flat: list = []
    if isinstance(messages, dict):
        for field, field_errors in messages.items():
            if isinstance(field_errors, list):
                flat.extend(str(m) for m in field_errors)
            else:
                flat.append(str(field_errors))
    elif isinstance(messages, list):
        flat.extend(str(m) for m in messages)
    return flat


@reset_password_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password_web():
    ticket = request.values.get("ticket", "")
    deep_link = f"truconnect://reset-password?ticket={ticket}" if ticket else None

    if not ticket:
        return render_template("reset_password_web.html", state="missing_ticket", deep_link=None)

    rate_limit_key = f"web_reset:{request.remote_addr or 'unknown'}"
    if not check_rate_limit(rate_limit_key, max_count=WEB_RESET_MAX_ATTEMPTS_PER_HOUR, window_seconds=3600):
        return render_template("reset_password_web.html", state="rate_limited", deep_link=deep_link), 429

    if request.method == "GET":
        if not PasswordResetService.validate_ticket(ticket):
            return render_template("reset_password_web.html", state="invalid", deep_link=deep_link)
        return render_template("reset_password_web.html", state="form", ticket=ticket, deep_link=deep_link)

    form_data = {
        "ticket": ticket,
        "newPassword": request.form.get("newPassword", ""),
        "confirmPassword": request.form.get("confirmPassword", ""),
    }
    try:
        data = _reset_password_schema.load(form_data)
    except MarshmallowValidationError as exc:
        errors = _flatten_errors(exc.messages)
        return render_template(
            "reset_password_web.html", state="form", ticket=ticket, deep_link=deep_link, errors=errors
        )

    try:
        PasswordResetService.reset_password(ticket=data["ticket"], new_password=data["new_password"])
    except TicketInvalidError:
        return render_template("reset_password_web.html", state="invalid", deep_link=deep_link)

    return render_template("reset_password_web.html", state="success", deep_link=None)