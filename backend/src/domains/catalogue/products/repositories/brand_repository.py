"""
Brand lookups, including the alias table that makes "COKE" resolve.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from src.domains.catalogue.products.models.brand import Brand, BrandAlias
from src.extensions import db


class BrandRepository:
    @staticmethod
    def get_by_slug(slug: str) -> Optional[Brand]:
        if not slug:
            return None
        return Brand.query.filter_by(slug=slug, is_deleted=False).first()

    @staticmethod
    def resolve(slug: str) -> Optional[Brand]:
        """The brand a supplier meant, whether they used its real name or
        the shorthand everyone actually writes.

        THE REAL NAME IS TRIED FIRST. An alias is a convenience; the
        canonical slug is the truth, and checking it first means adding a
        careless alias can never shadow a real brand.
        """
        brand = BrandRepository.get_by_slug(slug)
        if brand:
            return brand

        alias = BrandAlias.query.filter_by(alias_slug=slug, is_deleted=False).first()
        if not alias:
            return None
        return Brand.query.filter_by(id=alias.brand_id, is_deleted=False).first()

    @staticmethod
    def get_or_create(name: str, slug: str) -> Brand:
        existing = BrandRepository.get_by_slug(slug)
        if existing:
            return existing
        brand = Brand(name=name.strip(), slug=slug)
        db.session.add(brand)
        db.session.flush()
        return brand

    @staticmethod
    def add_alias(brand_id: str | UUID, alias_slug: str) -> Optional[BrandAlias]:
        """Idempotent -- adding an alias twice is a no-op rather than a
        constraint violation, since the callers are imports and seed
        scripts that legitimately run more than once."""
        if not alias_slug:
            return None
        existing = BrandAlias.query.filter_by(alias_slug=alias_slug, is_deleted=False).first()
        if existing:
            return existing
        alias = BrandAlias(alias_slug=alias_slug, brand_id=brand_id)
        db.session.add(alias)
        db.session.flush()
        return alias
