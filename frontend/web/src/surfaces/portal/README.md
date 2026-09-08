# `portal/`

The supplier hub: shell, navigation, and page compositions for
`app/(portal)/`.

Empty until the backend is ready. The portal's core is catalogue management,
and building it before `SupplierOffer` and the catalogue table settle means
building it twice.

## What the portal is for

**Setup and desk work** — catalogue, price files, terms, profile, analytics.
Things needing a keyboard, a wide screen, and a file picker.

**Daily operations stay in the app** — orders, cash decisions, notifications.
Things that need the person wherever they are.

The split is by **task, not by supplier size**. A supplier of any size uses
both surfaces; which one dominates depends on how they work.

## First screens, in order

1. Catalogue list
2. CSV import: upload, column map, preview, commit
3. Orders

Not a dashboard. A dashboard is the thing that feels like progress and is not.
