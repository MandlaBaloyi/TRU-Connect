# `design-system/` — layer 1

Visual building blocks with **zero TruConnect knowledge**. If a component
here mentions a supplier, an offer, or an order, it is in the wrong layer.

That constraint is the whole value: everything here works unchanged in the
supplier portal, the admin control centre, and anything built later.

| Folder | What goes in it |
|---|---|
| `tokens/` | Colours, spacing, type scale. Mirrored from the mobile theme. |
| `primitives/` | One-element building blocks: Button, Input, Field, Badge, Wordmark |
| `patterns/` | Compositions of primitives: DataTable, EmptyState, PageHeader, Pagination |
| `icons/` | Icon components |

**May not import:** `surfaces/`, `domains/`, `api/`.

## Primitive or pattern?

A primitive is one thing (`<Button>`). A pattern arranges several into a
shape that recurs (`<DataTable>` = header + rows + empty state + pagination).
If you are unsure, start in `primitives/` and promote it when a second
screen needs the same arrangement.
