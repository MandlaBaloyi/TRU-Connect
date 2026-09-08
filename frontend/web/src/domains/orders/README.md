# `orders/`

Incoming orders, their state, and their history.

Empty until the portal is built.

**Payment method selects the path, not supplier size:**

- **Direct** (cash, EFT) — the order is a *request*. Accept/decline is real,
  because the supplier is releasing stock against an unsecured promise.
- **Digital** — the order is a *purchase*. Money already moved, so there is
  nothing to accept. Declining becomes refund and cancel.

One engine, two paths. See V2_00 section 2.4.
