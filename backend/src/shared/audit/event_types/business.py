"""
Business's own audit event vocabulary -- domains/business/stock_order
is the publisher today (a business role action -- building and
submitting a cart), Security's audit service is the consumer, same
"both import from here, neither imports the other" shape as every
other domain's event_types file.

Named business.py, not stock_order.py -- events are organized by
WHICH ROLE the action belongs to (matching supplier.py's own
precedent), not by the specific feature name. A stock order is a
business-role action; a future business-side feature would add its
own events to this SAME file, not get a new one.

ORDER_LIMIT_EXCEEDED matters beyond a rejected request: repeated
attempts from the same account are a real, security-relevant signal
worth being able to query later (a business probing where the
boundary sits), not just a 409 response that vanishes the moment the
request finishes.
"""
from __future__ import annotations

import enum


class BusinessAuditEvent(str, enum.Enum):
    ORDER_SUBMITTED = "business.order_submitted"
    ORDER_LIMIT_EXCEEDED = "business.order_limit_exceeded"
    CHECKOUT_RATE_LIMITED = "business.checkout_rate_limited"
