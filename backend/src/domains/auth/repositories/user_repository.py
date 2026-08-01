"""
User Repository.
Ref: continuation master prompt -- repositories ONLY talk to SQLAlchemy;
no business rules here.

hard_delete is new (Auth Hardening master prompt, Objective 2). Every
other method is UNCHANGED.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from src.core.base_model import utcnow
from src.extensions import db
from src.domains.auth.models.user import User


class UserRepository:
    @staticmethod
    def get_by_id(user_id: str | UUID) -> Optional[User]:
        return User.query.filter_by(id=user_id, is_deleted=False).first()

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        normalized = email.strip().lower()
        return User.query.filter_by(email=normalized, is_deleted=False).first()

    @staticmethod
    def exists_by_email(email: str) -> bool:
        return UserRepository.get_by_email(email) is not None

    @staticmethod
    def create(**kwargs) -> User:
        if "email" in kwargs and kwargs["email"] is not None:
            kwargs["email"] = kwargs["email"].strip().lower()
        user = User(**kwargs)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update_last_login(user: User) -> User:
        user.last_login_at = utcnow()
        db.session.commit()
        return user

    @staticmethod
    def hard_delete(user: User) -> None:
        """Permanently removes a user row (and, via each child table's
        ON DELETE CASCADE, their refresh tokens / OTP records / password
        reset tickets).

        Used ONLY for unverified accounts that exceeded
        UNVERIFIED_ACCOUNT_EXPIRY_HOURS without ever completing
        verification. Such an account never became a real, trust-bearing
        entity -- soft_delete() (used everywhere else, to preserve
        trust-relevant history) is deliberately NOT used here, because
        the `email` column has an UNCONDITIONAL unique constraint (not
        scoped to is_deleted=false); a soft-deleted row would leave that
        email permanently unable to be reused, exactly the "permanent
        reservation" problem this feature exists to prevent.
        """
        db.session.delete(user)
        db.session.commit()
