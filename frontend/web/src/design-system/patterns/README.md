# `patterns/`

Compositions of primitives that recur across screens: `DataTable`,
`EmptyState`, `PageHeader`, `Pagination`, `FileDropzone`.

Currently: `Section` — the vertical band a marketing page is built from
(composes `Container`, owns the top/bottom rhythm and the background tone).
It is here rather than in `primitives/` because it composes another
component and decides layout — the recurring *shape*, not a single element.

The rest wait on the portal, which creates the need for most of them.

Still domain-free: a `DataTable` takes columns and rows, it does not know
they are supplier offers.
