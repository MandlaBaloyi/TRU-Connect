"""
All database access for audit events — writes and every admin query.

Built to be the exact surface a future Security Control Center route
layer needs, so adding the API is a thin wrapper rather than a redesign:

  * search()             -> the Audit Events / Live Activity screens
  * get_timeline()       -> "user reports a problem, show me their story"
  * get_by_correlation() -> one multi-step flow stitched together
  * count_by_event()     -> dashboard tiles / charts
  * count_failed_logins_by_ip() -> Suspicious IP Addresses screen
  * get_locked_accounts()-> Locked Accounts screen

CURSOR PAGINATION, NOT OFFSET. Offset pagination degrades badly on a
table that only grows (page 500 makes the database walk 10,000 rows to
discard them), and it silently skips or duplicates rows when new events
arrive mid-browse — which on a live-activity feed is constant. Cursor
pagination is stable under concurrent inserts and stays fast at any depth.

AGGREGATES RUN IN SQL, NOT PYTHON. Counting via SQL rather than loading
rows and counting them in a loop is the difference between a dashboard
that stays fast at 10 million rows and one that times out.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from src.domains.security.models.audit_event import AuditEventRecord
from src.extensions import db


@dataclass
class AuditSearchFilters:
    """
    Every filter the control center can apply. All optional and
    combinable — the query is built from whichever are set.

    Defined as a dataclass rather than a long kwargs list so the future
    API route can deserialize query params straight into it, and so
    adding a filter later touches one place.
    """
    domain: Optional[str] = None
    module: Optional[str] = None
    event_name: Optional[str] = None
    event_names: Optional[list[str]] = None  # e.g. all login-related events
    category: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    actor_type: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
    email_contains: Optional[str] = None  # partial search for investigators
    ip_address: Optional[str] = None
    tenant_id: Optional[str] = None
    correlation_id: Optional[str] = None
    device_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class PageResult:
    """One page of results plus the cursor to fetch the next."""
    items: list
    next_cursor: Optional[str]
    has_more: bool


def _encode_cursor(timestamp: datetime, record_id: Any) -> str:
    """
    Cursor = (timestamp, id). The id is the tiebreaker: many audit events
    can share a timestamp to the microsecond under load, and paginating on
    timestamp alone would drop or repeat rows at page boundaries.
    """
    payload = json.dumps({"ts": timestamp.isoformat(), "id": str(record_id)})
    return base64.urlsafe_b64encode(payload.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, str]:
    payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    return datetime.fromisoformat(payload["ts"]), payload["id"]


class AuditRepository:
    """Stateless — all methods operate on the shared db.session."""

    # -- writes ---------------------------------------------------------

    @staticmethod
    def insert(record: AuditEventRecord) -> AuditEventRecord:
        """
        Single insert, committed immediately. Audit writes are deliberately
        NOT joined to the caller's transaction: if a login attempt rolls
        back, the record that it was attempted must still survive. That is
        the entire evidentiary point — a failed action is exactly what an
        investigator needs to see.
        """
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def insert_many(records: list[AuditEventRecord]) -> int:
        """Batch insert for the async/queued path — one round trip instead
        of N when the worker drains a backlog."""
        if not records:
            return 0
        db.session.bulk_save_objects(records)
        db.session.commit()
        return len(records)

    # -- queries: list / search -----------------------------------------

    @staticmethod
    def _apply_filters(query, filters: AuditSearchFilters):
        M = AuditEventRecord
        if filters.domain:
            query = query.filter(M.domain == filters.domain)
        if filters.module:
            query = query.filter(M.module == filters.module)
        if filters.event_name:
            query = query.filter(M.event_name == filters.event_name)
        if filters.event_names:
            query = query.filter(M.event_name.in_(filters.event_names))
        if filters.category:
            query = query.filter(M.category == filters.category)
        if filters.severity:
            query = query.filter(M.severity == filters.severity)
        if filters.status:
            query = query.filter(M.status == filters.status)
        if filters.actor_type:
            query = query.filter(M.actor_type == filters.actor_type)
        if filters.user_id:
            query = query.filter(M.user_id == filters.user_id)
        if filters.email:
            query = query.filter(M.email == filters.email)
        if filters.email_contains:
            query = query.filter(M.email.ilike(f"%{filters.email_contains}%"))
        if filters.ip_address:
            query = query.filter(M.ip_address == filters.ip_address)
        if filters.tenant_id:
            query = query.filter(M.tenant_id == filters.tenant_id)
        if filters.correlation_id:
            query = query.filter(M.correlation_id == filters.correlation_id)
        if filters.device_id:
            query = query.filter(M.device_id == filters.device_id)
        if filters.start_time:
            query = query.filter(M.timestamp >= filters.start_time)
        if filters.end_time:
            query = query.filter(M.timestamp <= filters.end_time)
        return query

    @staticmethod
    def search(
        filters: Optional[AuditSearchFilters] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> PageResult:
        """
        Primary admin query — newest first, cursor-paginated.

        `limit` is capped at 500 here rather than trusting the caller: an
        unbounded page size on an append-only table is a trivial way to
        exhaust memory, whether by accident or by a malformed admin request.
        """
        limit = max(1, min(limit, 500))
        M = AuditEventRecord
        query = db.session.query(M)

        if filters:
            query = AuditRepository._apply_filters(query, filters)

        if cursor:
            cursor_ts, cursor_id = _decode_cursor(cursor)
            # Strict "older than the cursor row" comparison, using id to
            # break timestamp ties deterministically.
            query = query.filter(
                db.or_(
                    M.timestamp < cursor_ts,
                    db.and_(M.timestamp == cursor_ts, M.id < cursor_id),
                )
            )

        query = query.order_by(M.timestamp.desc(), M.id.desc())
        # Fetch one extra row to determine has_more without a second COUNT
        # query — COUNT on a growing audit table is expensive and, for a
        # "is there a next page" boolean, wasteful.
        rows = query.limit(limit + 1).all()

        has_more = len(rows) > limit
        items = rows[:limit]
        next_cursor = (
            _encode_cursor(items[-1].timestamp, items[-1].id)
            if items and has_more else None
        )
        return PageResult(items=items, next_cursor=next_cursor, has_more=has_more)

    @staticmethod
    def get_timeline(email: str, limit: int = 100) -> list:
        """
        "A user says their email has a problem" — the whole story for one
        address, newest first. This is the single most common
        investigation entry point, which is why email has its own
        composite index with timestamp.
        """
        return (
            db.session.query(AuditEventRecord)
            .filter(AuditEventRecord.email == email)
            .order_by(AuditEventRecord.timestamp.desc())
            .limit(min(limit, 500))
            .all()
        )

    @staticmethod
    def get_by_correlation(correlation_id: str) -> list:
        """
        One logical flow stitched together — e.g. a single registration
        producing REGISTER_SUCCESS, OTP_CREATED, OTP_SENT, OTP_VERIFIED as
        four rows. Ascending here (not descending) because a flow reads
        forward as a narrative.
        """
        return (
            db.session.query(AuditEventRecord)
            .filter(AuditEventRecord.correlation_id == correlation_id)
            .order_by(AuditEventRecord.timestamp.asc())
            .all()
        )

    # -- queries: aggregates for dashboard tiles -------------------------

    @staticmethod
    def count_by_event(
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict[str, int]:
        """Event-name -> count. Powers the dashboard's breakdown chart."""
        M = AuditEventRecord
        query = db.session.query(M.event_name, db.func.count(M.id))
        if start_time:
            query = query.filter(M.timestamp >= start_time)
        if end_time:
            query = query.filter(M.timestamp <= end_time)
        return dict(query.group_by(M.event_name).all())

    @staticmethod
    def count_by_severity(
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict[str, int]:
        M = AuditEventRecord
        query = db.session.query(M.severity, db.func.count(M.id))
        if start_time:
            query = query.filter(M.timestamp >= start_time)
        if end_time:
            query = query.filter(M.timestamp <= end_time)
        return dict(query.group_by(M.severity).all())

    @staticmethod
    def count_failed_logins_by_ip(
        since: datetime,
        min_count: int = 1,
        limit: int = 50,
    ) -> list[tuple[str, int]]:
        """
        Powers the Suspicious IP Addresses screen, and is the query a
        Phase 2 brute-force detector will build on. Returns
        [(ip, count), ...] descending.
        """
        M = AuditEventRecord
        return (
            db.session.query(M.ip_address, db.func.count(M.id).label("attempts"))
            .filter(
                M.event_name == "auth.login_failed",
                M.timestamp >= since,
                M.ip_address.isnot(None),
            )
            .group_by(M.ip_address)
            .having(db.func.count(M.id) >= min_count)
            .order_by(db.text("attempts DESC"))
            .limit(limit)
            .all()
        )

    @staticmethod
    def count_failed_logins_by_email(
        since: datetime,
        min_count: int = 1,
        limit: int = 50,
    ) -> list[tuple[str, int]]:
        """
        The other half of brute-force analysis. Kept as a separate query
        from the IP version on purpose: one attacker hitting many accounts
        from one IP, and many IPs hitting one account (credential
        stuffing), are different attack shapes and neither is visible in
        the other's aggregation.
        """
        M = AuditEventRecord
        return (
            db.session.query(M.email, db.func.count(M.id).label("attempts"))
            .filter(
                M.event_name == "auth.login_failed",
                M.timestamp >= since,
                M.email.isnot(None),
            )
            .group_by(M.email)
            .having(db.func.count(M.id) >= min_count)
            .order_by(db.text("attempts DESC"))
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_recent_lockouts(since: datetime, limit: int = 100) -> list:
        """Powers the Locked Accounts screen."""
        return (
            db.session.query(AuditEventRecord)
            .filter(
                AuditEventRecord.event_name == "auth.login_locked",
                AuditEventRecord.timestamp >= since,
            )
            .order_by(AuditEventRecord.timestamp.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def count_events_over_time(
        since: datetime,
        bucket: str = "hour",
        event_name: Optional[str] = None,
    ) -> list[tuple[datetime, int]]:
        """
        Time-series for dashboard charts, bucketed in SQL via date_trunc.

        `bucket` is validated against an allow-list rather than
        interpolated freely — it lands inside a SQL function call, so an
        unchecked value would be an injection point.
        """
        if bucket not in ("minute", "hour", "day", "week", "month"):
            raise ValueError(f"Unsupported bucket: {bucket}")

        M = AuditEventRecord
        bucket_expr = db.func.date_trunc(bucket, M.timestamp).label("bucket")
        query = db.session.query(bucket_expr, db.func.count(M.id)).filter(M.timestamp >= since)
        if event_name:
            query = query.filter(M.event_name == event_name)
        return query.group_by(bucket_expr).order_by(bucket_expr).all()
