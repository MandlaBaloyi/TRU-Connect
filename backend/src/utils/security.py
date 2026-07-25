"""
Password security utilities.
Ref: backend master prompt, "SECURITY"; continuation master prompt,
Step 6 (Password Security).

hash_password/verify_password are unchanged from the Steps 1-4
foundation. validate_password_complexity and passwords_match are new
for Step 6.
"""
import re

import bcrypt


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage. NEVER store plain_password
    itself, and never log it."""
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password attempt against a stored bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def validate_password_complexity(password: str) -> list[str]:
    """Returns a list of human-readable complexity violations (an empty
    list means the password is valid).

    Deliberately mirrors the mobile app's PASSWORD_REGEX
    (frontend/mobile/src/constants/regex.ts: minimum 8 characters, at
    least one letter, at least one number) -- this is defense in depth,
    not a second, different policy. The client-side check is a UX
    convenience; this is the one that actually matters, since a request
    can always bypass the mobile app entirely.
    """
    errors: list[str] = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Za-z]", password):
        errors.append("Password must contain at least one letter.")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one number.")
    return errors


def passwords_match(password: str, confirm_password: str) -> bool:
    """Simple equality helper used by registration and future
    password-change flows. Exists as a named function (rather than an
    inline == check scattered across callers) so the comparison logic
    has exactly one place to change if it ever needs to (e.g. a future
    constant-time comparison requirement)."""
    return password == confirm_password
