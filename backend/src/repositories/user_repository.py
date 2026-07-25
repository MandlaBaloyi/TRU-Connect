"""
User Repository.
Ref: continuation master prompt, "ARCHITECTURE RULES" -- repositories are
the ONLY layer that talks to SQLAlchemy directly. No business rules live
here (duplicate-email checks, password hashing, etc. belong in
src/services/auth_service.py).
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from src.core.base_model import utcnow
from src.extensions import db
from src.models.user import User


class UserRepository:
    @staticmethod
    def get_by_id(user_id: str | UUID) -> Optional[User]:
        return User.query.filter_by(id=user_id, is_deleted=False).first()

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        """Case-insensitive lookup (Step 8 requirement) -- email is
        always normalised to lowercase on both write and read."""
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
