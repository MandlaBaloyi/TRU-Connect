# TruConnect Web

The whole TruConnect web presence: the public site, the supplier portal,
and later the admin control centre and a lender surface.

Next.js 16 (App Router) + TypeScript + Tailwind v4. Talks to the same
Flask API as the mobile app.

```bash
npm run dev        # http://localhost:3000
npm run build      # production build
npx tsc --noEmit   # typecheck
npx eslint .       # lint + architecture boundaries
```

## Who this is for

**Suppliers and TruConnect staff. Not businesses.**

A business has no web surface and no sign-in, deliberately — their phone
is with them all day and their problem does not require a desk. Every
call to action on the public site resolves to exactly two places: get the
app, or sign in as a supplier. See `docs/v2/V2_00_ARCHITECTURE_EVOLUTION.txt`
section 2.9.

The supplier/web split is **by task, not by supplier size**:

- **Web** — setup and desk work. Catalogue, price files, terms, profile.
- **App** — daily operations. Orders, cash decisions, notifications.

A supplier of any size uses both.

## Architecture

Layers, with one rule:

```
surfaces/  ──▶  domains/  ──▶  api/ + design-system/  ──▶  lib/ + config/

                 IMPORTS ONLY EVER POINT RIGHT.
```

| Layer | Holds | Never imports |
|---|---|---|
| `design-system/` | Tokens, primitives, patterns. Zero TruConnect knowledge. | surfaces, domains, api |
| `api/` | HTTP transport, envelope handling, `ApiError`. No React. | surfaces, domains, design-system |
| `domains/` | Business logic and data by bounded context. No layout. | surfaces |
| `surfaces/` | Per-audience UI. Composes the layers below. | *(other surfaces)* |
| `lib/`, `config/` | Pure utilities, env, route constants. | everything above |

**This is enforced, not documented and hoped for.** `eslint.config.mjs`
fails the build on a violation — the same discipline the backend applies
to `src/shared/finance/`, which is AST-parsed and rejected if it imports
outside its allowlist.

### Why `domains/` is separate from `surfaces/`

This is the split that matters most. The admin control centre's biggest
job will be the **catalogue match-review queue** — the same catalogue
domain the supplier portal uses. Same types, same API, same per-unit
price logic, different UI.

If catalogue logic lived under `surfaces/portal/`, admin would have to
duplicate it or reach sideways. It doesn't, so admin will compose what
already exists. Lenders later work the same way: a lender reads order
history, and `domains/orders/` is already there.

## Tree

```
app/                            ROUTES ONLY. Thin files.
  layout.tsx                    <html>, <body>, fonts. No chrome.
  (marketing)/                  public, static, indexed
    layout.tsx                  SiteHeader + SiteFooter
    page.tsx  suppliers/  about/  contact/  (legal)/
  (auth)/                       sign-in, sign-up, verify, forgot
    layout.tsx                  bare centred shell
  (portal)/                     SUPPLIER. auth + role guard.        [pending]
    dashboard/ catalogue/ imports/ orders/
    storefront/ profile/ integrations/ settings/
  api/                          route handlers (cookie exchange, CSRF)

src/
  design-system/  tokens/  primitives/  patterns/  icons/
  api/            client.ts  query-client.ts  endpoints/
  domains/        auth/  catalogue/  imports/  orders/
                  storefront/  supplier-profile/
  surfaces/       marketing/  portal/  admin/                       [admin later]
  config/         env.ts  routes.ts
  lib/            pure utilities
  types/
```

Chrome belongs to the route group that owns it. The root layout is
`<html>`, `<body>` and fonts and nothing else — an earlier version put
the marketing header there, which would have leaked it into the portal.

## Not wired yet

**Authentication.** The sign-in and sign-up forms are real and validate,
but `domains/auth/services/authApi.ts` throws rather than submitting.

A browser must not hold a bearer token: anything reachable from
JavaScript is readable by any XSS, and a stolen supplier token is a
stolen catalogue. The portal needs an httpOnly, Secure, SameSite cookie
plus CSRF — backend work that has not landed (V2_00 section 2.10).
`api/client.ts` is written against that shape.

Until then the forms say they are not connected. A form that appears to
log you in and does not is worse than one that admits it.

## Conventions

- **Brand tokens are mirrored from the mobile theme, not imported.** A
  React Native app and a Next app cannot share a module without
  extracting a package, and a package is not worth its weight for nine
  hex values. Change a colour here, change it there. Same
  hand-kept-in-sync discipline as the backend's `row_validator.py` and
  its TypeScript counterpart.
- **`NEXT_PUBLIC_` means public.** It is inlined into the browser bundle
  at build time. Never put a secret behind one.
- **Marketing imagery comes from Cloudinary**, not `public/` — so it can
  change without a deploy and be transformed per device.

## Going monorepo later

Not now — one app, no extra tooling. But the seams are cut for it. If
admin needs to be physically separate so nothing admin-shaped ever ships
in a public bundle, `design-system/`, `api/` and `domains/` extract into
`packages/` and admin becomes `apps/admin/`. Hours, not weeks, because
the boundaries are already enforced.
