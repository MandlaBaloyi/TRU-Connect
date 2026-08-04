"""
All database access for audit events. Relocated from
security/repositories/ to security/audit/repositories/ -- content
unchanged except its own cross-reference to the model, which now points
to the model's new nested location.
"""

from __future__ import annotations

from src.domains.security.audit.models.audit_event import AuditEventRecord
from src.extensions import db


class AuditRepository:
    @staticmethod
    def insert(record: AuditEventRecord) -> AuditEventRecord:
        db.session.add(record)
        db.session.commit()
        return record
