# `src/` — the layer model

```
surfaces/  ──▶  domains/  ──▶  api/ + design-system/  ──▶  lib/ + config/
```

**Imports only ever point right.** Never back up the chain, never sideways
between siblings.

`eslint.config.mjs` enforces this. A violation fails lint, not code review.
Try it: import `@/api/client` from a file in `design-system/` and run
`npx eslint .` — it will refuse and name the rule.

| Folder | What lives here | One-line test |
|---|---|---|
| `design-system/` | Buttons, inputs, tables, colour tokens | Would this make sense in a completely different product? |
| `api/` | HTTP transport, the envelope, `ApiError` | Does it know what a supplier is? Then it does not go here. |
| `domains/` | Business logic and data, by subject | Would both the portal and admin need this? |
| `surfaces/` | Screens and shells, by audience | Is this a specific page for a specific person? |
| `config/` | Env vars, route constants | — |
| `lib/` | Pure helpers with no dependencies | Could this be published as a standalone utility? |
| `types/` | Shared TypeScript types | — |

## Why the layers exist

Not tidiness. Each edge prevents something concrete:

- **`design-system/` knows nothing about TruConnect** so the admin control
  centre and a future lender surface can reuse it. A Button that imports a
  catalogue type is a Button only the portal can use.
- **`domains/` is separate from `surfaces/`** because the admin match-review
  queue will use the *same* catalogue logic as the supplier portal. If that
  logic lived under `surfaces/portal/`, admin would have to duplicate it.
- **`api/` is separate from everything** so the cookie-versus-bearer decision
  lives in exactly one file.
