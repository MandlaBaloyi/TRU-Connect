# `config/`

Environment values and route constants, read and validated in one place
instead of scattered `process.env` reads.

| File | What it holds |
|---|---|
| `env.ts` | API base URL, Cloudinary cloud name |
| `routes.ts` | Every internal path |

## `NEXT_PUBLIC_` is a declaration, not a convenience

Anything with that prefix is **inlined into the browser bundle at build
time**. It is public, permanently, to anyone who opens devtools. Never put a
secret behind one.

Server-only values belong in a plain env var read inside a route handler or
server component, where the bundle never sees them. The Cloudinary *cloud
name* is public by design; the Cloudinary *API secret* stays on the Flask
backend, which is what signs uploads.

## Why `routes.ts`

A route typo is a 404 that no reviewer catches and no test fails on.
Referencing paths through one object makes it a compile error instead, and
when a route moves it moves once.
