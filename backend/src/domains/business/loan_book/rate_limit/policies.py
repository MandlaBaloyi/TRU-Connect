"""
Loan Book's own rate-limit policies — NOT IMPLEMENTED YET (Phase 2).

Follow auth/rate_limit/policies.py's exact shape when this gets built:
named limit constants, any needed custom key_func, and a
RATE_LIMIT_AUDIT_EVENTS mapping registered into
security/rate_limit/responses.py's shared registry at app-boot time
(see src/__init__.py's _register_error_handlers).
"""
