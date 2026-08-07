# Order Book Backend — Handoff Notes

Built by mirroring Loan Book's real code exactly: same folder shape
(api/models/repositories/schemas/services/utils — no algorithms/commands/
events/queries/validators, per the earlier agreed decision), same
ownership pattern, same Money discipline, same history-log reasoning.

## What's verified, and how (be honest about the limits)

**Could NOT run the real test suite.** This sandbox couldn't install
Postgres (the Ubuntu security mirror 404'd on the exact package
version needed), and this project's own testing rules correctly forbid
SQLite (no schema-qualified table support). So `test_ownership.py` and
`test_api_ownership.py` are written, syntax-checked, and shaped exactly
like Loan Book's proven-passing tests — but genuinely **not yet run
against a real database by me.** Run them yourself before trusting them:

```
python -m pytest tests/domains/business/order_book/ -v
```

**What WAS actually verified in this environment:**
- Every new file syntax-compiles cleanly (`py_compile`).
- The real Flask app boots end-to-end: `create_app("testing")` +
  `db.configure_mappers()` resolves every model, every foreign key
  (including confirming `Order.customer_id` now correctly targets
  `business.order_book_customers.id`, Order Book's own table — checked
  directly via `Order.__table__.c.customer_id.foreign_keys`, not
  assumed), and registers all 17 order-book routes — this catches
  typos, bad imports, and wrong table/column references without
  needing a live database.
- All 5 existing architecture tests still pass (`tests/architecture/`),
  confirming Order Book's use of `shared.finance` doesn't violate the
  Finance Engine's isolation boundary.
- The exact `Money`/`multiply`/`total` calls used in `create_order`
  were run directly against the real `shared.finance` module and
  produce the right cents.
- The pure calc functions (`trash_retention.py`, `auto_clear_window.py`)
  were run directly with real assertions, not just imported.

## Customer independence — resolved

**Order Book now has its own `order_book_customers` table**, fully
independent of Loan Book's `business.customers`. This replaces the
earlier "reuse Loan Book's Customer" decision flagged in the previous
round — after review, the answer was to keep the two features
independent. Deleting or restoring a customer in Order Book has zero
effect on Loan Book, and vice versa. **No Loan Book file was touched**
to make this change — confirmed with a byte-for-byte diff against your
original upload.

## Deliberately NOT wired yet (flagged, not silently skipped)

**Auto-clear sweep has no real scheduler.** `AutoClearService.run_sweep()`
exists and does the right thing when called, and there's a manual
`POST /api/v1/order-book/balances/auto-clear-sweep` route to trigger it
by hand — but nothing calls it on a timer. Wiring it into
`master_scheduler/` (the same pattern every other domain's scheduled
job already uses) is real, separate follow-up work.

**"Today" is UTC, not the business's local day.** `_today()` in
`order_book_service.py` uses the server's UTC date for per-day order
numbering and revenue grouping. The frontend's mock currently uses the
device's local date. These will disagree near a day boundary until
reconciled — either by passing the business's local date explicitly
from the client, or by storing a business timezone once one exists.

## Not yet done (out of scope for this round)

- **Performance rollup endpoint** (the 3D/7D/30D/3M/1Y screen) — the
  frontend computes this client-side from daily-revenue entries
  already; a dedicated backend endpoint wasn't built this round since
  the existing `/balances/daily-revenue` endpoint gives the frontend
  everything it needs to keep doing that same computation once wired.
- **No migration has been run against your actual dev database.** The
  migration file is written and chained correctly onto your real
  current head (`d3e4f5a6b7c8`), but `flask db upgrade` needs to
  actually be run on your machine — I could not do that here either,
  for the same Postgres-availability reason above.

## Recommended next steps, in order

1. Run `flask db upgrade` against your real dev DB, watch it apply cleanly.
2. Run the ownership tests for real: `python -m pytest tests/domains/business/order_book/ -v`
3. Confirm you're OK with the shared-customer consequence above.
4. Only then: wire the frontend's `httpOrderBookApi.ts` to these real
   routes (currently every function there still throws
   "not implemented yet" on purpose).
