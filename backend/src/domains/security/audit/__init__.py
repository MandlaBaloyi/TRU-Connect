"""
Audit -- nested to match Business's proven per-feature shape
(models/repositories/services/schemas/rules), the same convention
already used for business/loan_book/, business/business_profile/, etc.
Previously these files sat flat and mixed directly inside
security/models/, security/repositories/, security/services/, and
security/rules/ -- fine while Audit was the only thing in those folders,
but not ready for the volume this domain is expected to grow into
(detection/, analytics/, monitoring/ are all reserved siblings that will
eventually want their own real content in those SAME flat folders).

security/detection/ stays a sibling to this package, not nested inside
it -- detection and audit are related but distinct responsibilities.
security/rules/thresholds.py stays OUTSIDE this package too: it's a
general Auth threshold (how many days before an unverified email
expires), not audit-specific, even though it happens to sit in the
security domain.
"""
