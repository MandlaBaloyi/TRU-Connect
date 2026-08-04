# TRU Connect Backend — Testing Reference

**Status: 179/179 passing** (full suite, real Postgres, confirmed).

This document explains what each test group actually verifies, why the
database setup exists in the shape it does, and the specific bugs this
project's real test runs caught — kept here so the reasoning survives
past whoever originally debugged it.

For copy-paste commands, see `tests.txt`. This file is the "why."

---

## The shape of the suite

```
tests/
├── architecture/           Boundary enforcement — no database
├── shared/finance/         Money engine — no database
├── domains/
│   ├── auth/
│   │   ├── jobs/            Scheduled cleanup job — NEEDS DATABASE
│   │   └── schedulers/      Auth's own job list — no database
│   ├── platform/schedulers/ Master Scheduler — no database
│   └── security/
│       ├── audit/           Mixed — see breakdown below
│       └── schedulers/      Job health monitoring — no database
├── conftest.py              Shared fixtures: app, client, db_session, make_user
└── test_auth.py             Full Auth integration — NEEDS DATABASE
```

**106 of 179 tests need zero database setup.** Only six files touch
Postgres directly: `test_cleanup_unverified_emails.py`,
`test_append_only.py`, `test_audit_repository.py`,
`test_audit_service.py`, and every integration test in `test_auth.py`.

---

## What each group actually proves

### Finance Engine (84 tests) — `tests/shared/finance/`

Every guarantee is executed, not just asserted:

- **No float ever touches money.** Rejected at every entry point —
  `Money()`, `from_major_units()`, `multiply()`, `round_to_minor_units()`
  all refuse a float argument outright.
- **Allocation never loses a cent.** R100 split three ways produces
  `[3334, 3333, 3333]` — exactly 10000, never 9999 from naive division.
  Verified across 13 parametrized cases, including the genuinely awkward
  ones (1 cent split 3 ways, prime-number ratios).
- **Precision comes from the currency, not a global assumption.** ZAR
  (2 decimal places), JPY (0), BHD (3) are all tested against the same
  functions — nothing in the engine assumes `/100`.
- **Currency mismatches raise, never silently convert.** Adding ZAR to
  USD is a `CurrencyMismatchError`, not an invented exchange rate.
- **Real South African input parses correctly** — `"R 1 250,50"`,
  `"1.250,50"`, `"-R500.00"`, spaces as thousands separators, comma OR
  dot as decimal separator depending on position.

### Architecture boundaries (5 tests) — `tests/architecture/`

Parses the Finance Engine's own source with Python's AST (not a text
search — a regex would miss aliased or multi-line imports) and fails the
build if it ever imports a domain, `shared.audit`, `shared.security`,
`shared.queue`, Flask, or SQLAlchemy, or calls `float()`.

**Proven to actually fire, not just written:** a file deliberately
violating all five rules was added during development. All five tests
failed, each naming the exact file, line, and *why* it matters. Then the
violation was removed. This is what makes it a guardrail instead of a
comment nobody reads.

### Master Scheduler (15 tests) — `tests/domains/platform/schedulers/`

One shared execution engine; each domain declares its own jobs in its
own file (`domains/auth/schedulers/auth_scheduler.py`, etc.) rather than
the Master defining any job itself.

`test_registry_defines_no_jobs_itself` inspects the registry's actual
source code to confirm this structurally — the same discipline as the
Finance boundary tests, applied to "does the Master Scheduler run
business jobs? No."

### Audit — app-context fix (3 tests) — `test_audit_service.py`

**The original bug:** ASYNC-classified audit events (OTP created, token
created) were silently failing with `RuntimeError: Working outside of
application context`. The deferred write ran on a background thread
*after* the originating request's Flask context had already ended.

**The fix:** `register(app)` now captures the real Flask app and wraps
every deferred write in `app.app_context()` explicitly, regardless of
which thread ends up executing it.

**Why the test is trustworthy:** it uses a genuine `threading.Thread`,
not a same-thread simulation — this test would have failed with the
original bug and only passes because the fix is real.

### Append-only trigger (2 tests) — `test_append_only.py`

A real Postgres trigger rejects `UPDATE` and `DELETE` against
`security.audit_events`. Both tests attempt the mutation directly and
assert Postgres itself refuses it — compliance enforced at the database
layer, not just by application convention.

**A real ordering bug lived here, worth knowing about:** the shared
`app` fixture's `db.create_all()` / `db.drop_all()` only know about
SQLAlchemy model metadata. The append-only trigger is pure migration
DDL, never part of the model. The first test in a run got lucky (the
table still carried the trigger from `flask db upgrade`), but
`drop_all()` in that test's teardown dropped the table — and the
trigger with it — so the *next* test's `create_all()` rebuilt a bare
table with no trigger at all. `DELETE` silently succeeded when it should
have been rejected.

**Fixed** with a file-scoped `autouse=True` fixture that re-applies the
exact trigger DDL before every test in `test_append_only.py`
specifically — not at the directory level, which was tried first and
broke `test_audit_context.py`'s unrelated, database-free fixture by
accident.

---

## Database setup — why each piece exists

| Step | Why |
|---|---|
| Dedicated `tru_connect_test` database | Tests insert fake users and `test_append_only.py` deliberately fires real `UPDATE`/`DELETE` statements — never point tests at a database also used for real development data. |
| `OWNER tru_connect_app` | The app's real user is deliberately restricted (no `CREATEDB`) — correct security practice. Ownership grants full rights *inside* this one database without loosening privileges anywhere else. |
| 8 schemas created manually | Every domain's models target a specific Postgres schema (`__table_args__ = {"schema": "..."}`); `db.create_all()` can't create a table in a schema that doesn't exist yet. |
| `flask db upgrade` against the test DB | `db.create_all()` only builds tables from model metadata — it has no concept of migrations, so it never creates the append-only trigger. Only Alembic knows about that. |
| URL-encoding the password | Any of `@ : / ? # %` in a password breaks a plain connection-string URL, since those characters are structurally meaningful in a URI (a literal `@` gets misread as the separator before the host). |

---

## Fixture reference — `tests/conftest.py`

| Fixture | Provides | Notes |
|---|---|---|
| `app` | A real Flask app, `create_all()` on setup, `drop_all()` on teardown | Promoted unchanged from what `test_auth.py` already proved working — not reinvented |
| `client` | `app.test_client()` | For HTTP-level integration tests |
| `db_session` | `db.session`, inside `app`'s active context | For tests that need direct DB access without going through a route |
| `make_user` | Factory building a `User` row with sensible defaults | Required columns (`email`, `password_hash`, `role`) always get a value; everything else follows the model's own defaults unless overridden |

---

## Known harmless warnings

```
WARNING audit service: register() called twice -- ignoring
```
The double-registration guard working as designed — usually means more
than one `Flask` app got created in one test session. Not a real
problem.

```
InsecureKeyLengthWarning: The HMAC key is 23 bytes long...
```
Your test `JWT_SECRET_KEY` is short. Harmless for tests specifically,
but confirm your **real** dev/prod key (in `.env`, not the test config)
is a proper 32+ byte random value — generate with:
```
python -c "import secrets; print(secrets.token_hex(32))"
```