# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

Monorepo for **TRU Connect**, a two-sided mobile marketplace (informal-economy
businesses ↔ suppliers) that is part of the larger "TruePoint" platform.

- `backend/` — Flask + PostgreSQL API (application factory, domain-driven)
- `frontend/mobile/` — Expo / React Native app (Expo Router, TypeScript)
- `frontend/web/` — placeholder, empty
- `docs/` — authoritative product/architecture/API specs (see below)
- `database/`, `deployment/` — currently empty scaffolding
- `tests/backend/` — legacy location of `test_auth.py`; the live suite is `backend/tests/`
- `*_structure.txt`, `structure.txt`, `print_project_tree.py` — generated tree snapshots, not inputs

`docs/` is prose spec, not generated. `docs/00A_TRUEPOINT_PLATFORM_CONSTITUTION.txt`
is treated as the highest-authority design document; `docs/05_BACKEND_API_SPECIFICATION.txt`
defines the JSON envelope and is referenced directly from code comments.

## Backend (`backend/`)

### Commands

```
# from backend/, with .venv activated
$env:FLASK_APP = "app.py"          # PowerShell; bash: export FLASK_APP=app.py

python app.py                      # run dev server on 0.0.0.0:5000
flask db migrate -m "message"      # generate migration
flask db upgrade                   # apply migrations

pytest                             # full suite
pytest backend/tests/domains/network/orders            # one domain
pytest backend/tests/domains/network/orders/test_cart_and_checkout.py::test_name   # one test
pytest backend/tests/architecture                      # architecture boundary tests only
```

There is no configured linter/formatter and no `pytest.ini`/`pyproject.toml` —
`pytest` picks up `backend/tests/` by default when run from the repo root or `backend/`.

### Test database

Tests need a running PostgreSQL. Config is `TestingConfig` (`src/config.py`),
DB URL from `TEST_DATABASE_URL` or default
`postgresql+psycopg2://postgres:postgres@localhost:5432/tru_connect_test`.
`backend/tests/conftest.py` discovers every schema referenced in SQLAlchemy
metadata, runs `CREATE SCHEMA IF NOT EXISTS`, then `db.create_all()` — **tests
do not run migrations**, and drop/recreate schema per test. Email uses the
in-memory fake provider (`MAIL_PROVIDER=fake`, `MAIL_ASYNC=False`).

Notifications and some audit writes are dispatched through
`src/shared/queue`'s background thread pool. A test that triggers one (checkout,
connection request/approve) must wait for it or the write can land in the next
test's freshly-created schema. See the long comment in `conftest.py`.

### Architecture

**Application factory.** `src/__init__.py::create_app(env_name)` builds the app:
registers extensions (`src/extensions.py` — unbound `db`, `migrate`, `jwt`, `ma`),
registers every domain Blueprint explicitly, installs a single `AppError`
handler, then wires cross-cutting services and starts the master scheduler.
`app.py` is the WSGI entry point (`app:app` for gunicorn).

**Domain structure.** Code lives in `src/domains/<area>/<domain>/`, where area is
one of `auth`, `business`, `supplier`, `network`, `platform`, `security`,
`marketplace`, `trust`, `verification`. Each domain uses a consistent layout:
`api/` (Blueprint + routes), `services/` (business logic, raises `AppError`),
`repositories/` (DB access), `models/`, `schemas/` (Marshmallow), and optionally
`schedulers/`, `notification_templates/`, `rate_limit/`, `algorithms/`,
`providers/`, `webhooks/`, `config/`. Routes are thin: validate → call service →
`success_response(...)`; they never catch `AppError`.

**Shared vs domain.** `src/shared/` holds infrastructure that domains depend on
but which must not depend on domains: `finance/`, `media/`, `audit/`,
`notifications/`, `queue/`, `scheduling/`, `email/`, `cache/`, `security/`.
`src/core/` holds `exceptions.py` (the `AppError` hierarchy with stable `code`
strings), `responses.py` (the `{success, message, data | errors, code?}`
envelope), `decorators.py`, `base_model.py`.

**Isolation is enforced, not just documented.** `backend/tests/architecture/`
AST-parses `src/shared/finance/` and fails if it imports anything outside an
allowlist — "Finance is a leaf." Follow the same pattern: `shared/` code that
needs to react to a domain event does so via a registration hook the domain
calls (e.g. `create_app` registers `product_media_service.apply_scan_result`
with `shared.media`'s webhook dispatcher; `security` subscribes to scheduler
outcomes via `master_scheduler.runner.add_listener`). The coordinator never
imports the thing it coordinates.

**Master scheduler.** `src/master_scheduler/` (sibling of `core/`/`shared/`, not
inside any domain) owns the one APScheduler instance (`engine.py` is the only
file allowed to import apscheduler), the safe-execution wrapper (`runner.py`),
and startup (`trigger.py`, guarded against the Flask reloader's double process).
It defines **no jobs**. To add a scheduled job: write a `run() -> JobResult`
function in the owning domain, add a `JobSpec` to that domain's
`schedulers/<domain>_scheduler.py::JOB_SPECS`, and (only for a brand-new domain)
add that list to `registry.py::ALL_JOB_SPECS`.

**Auth decorators** (`src/core/decorators.py`): `login_required`,
`verified_required`, `active_account_required`, `fully_authenticated`,
`role_required("supplier")`, `permission_required(...)`. The
verified/active/fully variants deliberately re-query the DB every request rather
than trusting JWT claims. Supplier-only endpoints stack
`@fully_authenticated` + `@role_required("supplier")`.

**PostgreSQL uses multiple schemas** (per-domain), built from discrete
`POSTGRES_*` env vars (or `DATABASE_URL`). Payment providers (PayFast / manual)
sit behind `providers/` abstractions — services never import a concrete provider
by name.

## Frontend (`frontend/mobile/`)

### Commands

```
npm start            # expo start (Metro)
npm run android      # expo run:android
npm run ios          # expo run:ios
npm run typecheck    # tsc --noEmit   (the only check; no ESLint configured)
```

EAS build config is in `eas.json`; project is `truconnect` (`app.json`).

### Architecture

**Routing** is Expo Router file-based under `app/`, using route groups:
`(auth)/`, `(onboarding)/`, `(legal)/`, and `(dashboard)/business/(tabs)/...`.
Dashboards are role-split (`business` today; `supplier` scaffolding exists). The
authoritative role comes from the backend after login (`STORAGE_KEYS.USER_ROLE`),
not the onboarding picker.

**Feature code** lives in `src/features/<area>/<feature>/` (hooks, schemas,
services, components), separate from the route files in `app/` which stay thin.
Shared building blocks are in `src/components/`, `src/theme/` (react-native-paper),
`src/hooks/`, `src/services/`.

**API layer.** `src/services/api/apiClient.ts` is the shared Axios instance. It
unwraps the backend envelope (callers get the inner `data`), attaches the access
token, and throws a normalized `ApiError` carrying `status`, `errors`, and the
backend `code` (e.g. `"EMAIL_NOT_VERIFIED"`, `"ACCOUNT_LOCKED"`). Server state is
React Query (`src/services/api/queryClient.ts`); local state is Zustand; forms are
react-hook-form + Zod.

**Mock mode.** `USE_MOCK_API` (`src/constants/config.ts`) defaults **true** —
auth returns fake data instantly. Set `EXPO_PUBLIC_USE_MOCK_API=false` to hit the
real backend. `API_BASE_URL` comes from `EXPO_PUBLIC_API_BASE_URL`, then
`app.json` `extra.apiBaseUrl`, then a hardcoded LAN IP fallback. On a physical
device use your machine's LAN IP, not `localhost` (Flask already binds
`0.0.0.0`).

## Working in this codebase

Comments here are unusually long and narrative — they record past bugs, rejected
alternatives, and *why* a file lives where it does. When changing such a file,
keep that reasoning current rather than deleting it, and match the density of the
surrounding code.
