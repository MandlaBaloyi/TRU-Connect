"""
The shared rate limiter instance.

SAME PATTERN AS extensions.py (db/migrate/jwt/ma): instantiated here
WITHOUT binding to an app, bound via limiter.init_app(app) in
create_app(). This is what lets create_app() run more than once (real
app + a fresh instance per test) without limiter state leaking between
instances. Lives in this domain folder rather than extensions.py itself
because rate-limit POLICY is a security concern this domain owns, not a
generic cross-cutting extension like the database connection — but the
binding call in create_app() looks and behaves exactly like every other
extension's.

STORAGE: in-memory (Flask-Limiter's default), for Phase 1.

    THIS IS A DELIBERATE, DOCUMENTED LIMITATION, NOT AN OVERSIGHT:
    in-memory storage keeps its counters in this process's own memory.
    That is completely correct for the current single-process Flask
    dev server. It becomes WRONG the moment this app runs behind
    multiple worker processes or multiple horizontally-scaled
    instances (e.g. gunicorn -w 4, or 2+ deployed instances behind a
    load balancer) -- each process gets its OWN separate counter, so a
    "5 requests/minute" limit silently becomes "5 x N processes
    requests/minute" with no error and no warning.

    BEFORE THIS APPLICATION MOVES TO A MULTI-WORKER OR
    HORIZONTALLY-SCALED DEPLOYMENT, storage_uri below MUST be changed
    to a shared backend (Redis is the standard choice for
    Flask-Limiter -- storage_uri="redis://<host>:6379"). That is real,
    separate infrastructure work (a Redis instance to provision and
    operate), intentionally not done here per the approved Phase 1
    scope. Grep for "storage_uri" if you're looking for the one line
    that needs to change.

KEY FUNCTION: get_remote_address (IP-based) is the DEFAULT for every
route that doesn't override it. Login overrides this with a composite
IP+email key -- see policies.py's login_key_func for why.
"""
from __future__ import annotations

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],  # no blanket global limit -- every limited route opts in explicitly via @limiter.limit(...); see policies.py
    storage_uri="memory://",  # Phase 1 -- see module docstring above before changing deployment topology
    headers_enabled=True,  # adds RateLimit-* / Retry-After response headers, on top of the JSON body responses.py returns
)
