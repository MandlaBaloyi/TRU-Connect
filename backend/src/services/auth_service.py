"""
Authentication Service.
Ref: continuation master prompt, Steps 7-12. ALL business logic for
registration, login, JWT issuance, refresh-token rotation, and logout
lives here. Routes (src/api/auth_routes.py) call these methods and never
touch SQLAlchemy or JWT generation directly.

Steps 7-8 (register_business, register_supplier, login) are UNCHANGED
from the Phase 2 version. Steps 9-12 (_issue_tokens, refresh, logout) are
extended for refresh-token persistence, rotation, and revocation.
"""
from __future__ import annotations

import hashlib
from typing import Optional, Tuple

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jti

from src.core.base_model import utcnow
from src.core.exceptions import ConflictError, ForbiddenError, UnauthorizedError
from src.models.user import User, UserRole
from src.repositories.refresh_token_repository import RefreshTokenRepository
from src.repositories.user_repository import UserRepository
from src.utils.security import hash_password, verify_password


def _hash_jti(jti: str) -> str:
    """Same rationale as RefreshToken's own docstring: never store the
    raw refresh token or its raw jti, only a hash of it."""
    return hashlib.sha256(jti.encode("utf-8")).hexdigest()


class AuthService:
    # ------------------------------------------------------------------
    # Step 7 -- Registration (UNCHANGED from Phase 2)
    # ------------------------------------------------------------------

    @staticmethod
    def register_business(data: dict) -> Tuple[User, dict]:
        if UserRepository.exists_by_email(data["email"]):
            raise ConflictError("An account with this email already exists.")

        user = UserRepository.create(
            email=data["email"],
            password_hash=hash_password(data["password"]),
            role=UserRole.BUSINESS,
            first_name=data["first_name"],
            last_name=data["last_name"],
        )
        tokens = AuthService._issue_tokens(user)
        return user, tokens

    @staticmethod
    def register_supplier(data: dict) -> Tuple[User, dict]:
        if UserRepository.exists_by_email(data["email"]):
            raise ConflictError("An account with this email already exists.")

        user = UserRepository.create(
            email=data["email"],
            password_hash=hash_password(data["password"]),
            role=UserRole.SUPPLIER,
            first_name=data["owner_name"],
            last_name=None,
        )
        tokens = AuthService._issue_tokens(user)
        return user, tokens

    # ------------------------------------------------------------------
    # Step 8 -- Login (UNCHANGED from Phase 2)
    # ------------------------------------------------------------------

    @staticmethod
    def login(email: str, password: str) -> Tuple[User, dict]:
        user = UserRepository.get_by_email(email)

        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.")

        if not user.is_active:
            raise ForbiddenError("This account has been deactivated.")

        UserRepository.update_last_login(user)
        tokens = AuthService._issue_tokens(user)
        return user, tokens

    # ------------------------------------------------------------------
    # Step 9 -- JWT issuance, extended for Step 11 (persistence)
    # ------------------------------------------------------------------

    @staticmethod
    def _issue_tokens(
        user: User, device_id: Optional[str] = None, ip_address: Optional[str] = None
    ) -> dict:
        """Issues an access + refresh token pair. Every refresh token
        issued here also gets a corresponding RefreshToken row (Step 11)
        so it can later be looked up and revoked -- access tokens remain
        fully stateless (Step 12 rule), only refresh tokens are tracked.
        """
        additional_claims = {"role": user.role.value}
        access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
        refresh_token = create_refresh_token(identity=str(user.id), additional_claims=additional_claims)

        jti = get_jti(refresh_token)
        expires_at = utcnow() + current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]
        RefreshTokenRepository.create(
            user_id=user.id,
            jti_hash=_hash_jti(jti),
            expires_at=expires_at,
            device_id=device_id,
            ip_address=ip_address,
        )

        return {"access_token": access_token, "refresh_token": refresh_token}

    # ------------------------------------------------------------------
    # Step 11 -- Refresh Token rotation
    # ------------------------------------------------------------------

    @staticmethod
    def refresh(current_jti: str, user_id: str, device_id: Optional[str] = None, ip_address: Optional[str] = None) -> dict:
        """Validates the presented refresh token against the database
        (not just its JWT signature/expiry, which flask_jwt_extended
        already checked before this method is called) and ROTATES it:
        the token just used is revoked, and a brand new access+refresh
        pair is issued. This means a refresh token can only ever be used
        once -- if a stolen refresh token is used by an attacker, the
        legitimate user's next refresh attempt will fail (the token was
        already revoked), which is a detectable signal of compromise
        even though this generator doesn't yet build an alerting system
        around that signal.
        """
        token_record = RefreshTokenRepository.get_by_jti_hash(_hash_jti(current_jti))

        if token_record is None or not token_record.is_valid():
            raise UnauthorizedError("Refresh token is invalid or has been revoked.")

        RefreshTokenRepository.revoke(token_record)

        user = UserRepository.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found.")

        return AuthService._issue_tokens(user, device_id=device_id, ip_address=ip_address)

    # ------------------------------------------------------------------
    # Step 12 -- Logout
    # ------------------------------------------------------------------

    @staticmethod
    def logout(user_id: str, refresh_token_jti: Optional[str] = None) -> None:
        """Single-device logout when the caller provides the specific
        refresh token's jti (revokes only that one). Falls back to
        revoking EVERY active refresh token for the user when no
        specific jti is provided -- a safe default, and currently the
        path the mobile app actually exercises, since
        frontend/mobile/src/services/auth/authService.ts's logout()
        does not yet send a refresh token in the request body. Update
        that function to POST {"refresh_token": "..."} for true
        single-device semantics; until then this safe fallback is what
        runs.
        """
        if refresh_token_jti:
            token_record = RefreshTokenRepository.get_by_jti_hash(_hash_jti(refresh_token_jti))
            if token_record is not None and str(token_record.user_id) == str(user_id):
                RefreshTokenRepository.revoke(token_record)
            return

        RefreshTokenRepository.revoke_all_for_user(user_id)

    @staticmethod
    def get_current_user(user_id: str) -> User:
        user = UserRepository.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found.")
        return user
