"""
Threat detection — PHASE 1: STRUCTURE ONLY, NO DETECTORS.

Deliberately empty of real detection logic. Phase 1 builds the audit
platform (the record of what happened); Phase 2 builds the intelligence
that reads it. Shipping interfaces now fixes the shape detectors must
conform to, so Phase 2 adds detectors without redesigning anything.

IMPORTANT — WHAT DETECTION IS NOT RESPONSIBLE FOR: account lockout after
N failed logins stays in the Authentication domain, synchronous and
immediate. It is a first-boundary control that must act during the
request; routing it through an audit-then-detect pipeline would leave a
window in which an attacker keeps guessing while detection catches up.

Detection's job is the layer above that: patterns a single-request check
cannot see — credential stuffing across many accounts, distributed
attempts from many IPs, impossible travel, device anomalies.
"""
