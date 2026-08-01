"""
Password security utilities.
Ref: backend master prompt, "SECURITY" -- bcrypt hashing; never expose
password hashes.
"""
import re

import bcrypt

# Mirrors frontend/mobile/src/constants/regex.ts PASSWORD_REGEX exactly.
# The server must never be more permissive than the client, or a request
# that bypasses the app could set a weaker password than the UI promises.
_SPECIAL_CHARACTERS = r"@$!%*?&.#^()_\-+="


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage. NEVER store plain_password
    itself, and never log it."""
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password attempt against a stored bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def validate_password_complexity(password: str) -> list[str]:
    """Returns a list of human-readable complexity violations (empty list
    means valid).

    Kept deliberately in sync with the mobile client's PASSWORD_REGEX so a
    password accepted by one is accepted by the other. If you change one,
    change both.
    """
    errors: list[str] = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one number.")
    if not re.search(rf"[{_SPECIAL_CHARACTERS}]", password):
        errors.append("Password must contain at least one special character.")

    return errors


def passwords_match(password: str, confirm_password: str) -> bool:
    """Equality helper used by registration and password-change flows."""
    return password == confirm_password