"""
MatchAlias reads and writes -- tier 1 of the ladder.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from src.domains.catalogue.matching.models.match_alias import AliasSource, MatchAlias
from src.extensions import db


class MatchAliasRepository:
    @staticmethod
    def get(matching_key: str) -> Optional[MatchAlias]:
        if not matching_key:
            return None
        return MatchAlias.query.filter_by(matching_key=matching_key, is_deleted=False).first()

    @staticmethod
    def record_hit(alias: MatchAlias) -> MatchAlias:
        """times_seen is how you find out which aliases are worth a
        human's attention and which are stale enough to delete. Not used
        in matching itself."""
        alias.times_seen = (alias.times_seen or 0) + 1
        return alias

    @staticmethod
    def upsert(
        *,
        matching_key: str,
        source_text: str,
        product_id: str | UUID,
        source: AliasSource,
    ) -> Optional[MatchAlias]:
        """Learn, or re-confirm.

        AN EXISTING ALIAS IS NEVER REPOINTED AT A DIFFERENT PRODUCT here.
        One text means one product; if a new match disagrees with a
        recorded alias that is a contradiction a person should see, not
        something a background import should silently resolve by
        overwriting. The existing row is returned unchanged.
        """
        if not matching_key or not product_id:
            return None

        existing = MatchAliasRepository.get(matching_key)
        if existing:
            MatchAliasRepository.record_hit(existing)
            return existing

        alias = MatchAlias(
            matching_key=matching_key,
            source_text=(source_text or "")[:300],
            product_id=product_id,
            source=source,
            times_seen=1,
        )
        db.session.add(alias)
        db.session.flush()
        return alias
