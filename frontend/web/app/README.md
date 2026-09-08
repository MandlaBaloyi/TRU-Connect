# `app/` — routes only

Every file here is thin. Pages compose from `src/surfaces/`; they do not
contain logic.

## Route groups

A folder in parentheses groups routes **without appearing in the URL**.
`app/(marketing)/suppliers/page.tsx` serves `/suppliers`, not
`/(marketing)/suppliers`.

They exist so each audience owns its own layout, its own chrome, and its own
auth guard.

| Group | URL prefix | Chrome | Auth |
|---|---|---|---|
| `(marketing)` | none | site header + footer | none |
| `(marketing)/(legal)` | none | inherits marketing | none |
| `(auth)` | none | bare centred shell | none |
| `(portal)` | none | portal shell + nav | cookie + supplier role |

`(legal)` groups `/terms` and `/privacy` for organisation only — it adds no
layout of its own, so the pages keep the marketing header and footer.

## The root layout stays empty

`app/layout.tsx` is `<html>`, `<body>` and fonts. Nothing else.

An earlier version put the marketing header there, which meant the supplier
portal would have inherited a "Create a supplier account" button the moment
it existed. Chrome belongs to the group that owns it — that is what makes the
mistake impossible rather than merely unlikely.
