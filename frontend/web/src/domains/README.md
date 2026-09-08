# `domains/` — layer 2

Business logic and data, organised by **subject**, not by who looks at it.

**May not import:** `surfaces/`.

A domain folder typically holds:

```
<domain>/
  services/    calls api/, returns domain types
  hooks/       React Query hooks
  schemas/     validation
  types.ts
  components/  domain-specific pieces (an OfferCard, not a Button)
```

## Why this is not organised by audience

This is the split that matters most, and the reason is concrete.

The admin control centre's biggest job will be the **catalogue match-review
queue** — the same catalogue logic the supplier portal uses. Same types, same
API calls, same per-unit price maths, different screens.

If that logic lived under `surfaces/portal/`, admin would have to duplicate
it or reach sideways into another surface. It does not, so admin will compose
what already exists. Lenders later work the same way: a lender reads order
history, and `orders/` is already here.

Audiences differ in **presentation**, not in what an offer is. So audiences
split in `surfaces/`, and subjects split here.
