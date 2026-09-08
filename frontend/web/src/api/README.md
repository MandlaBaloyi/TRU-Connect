# `api/` — layer 1

HTTP transport. **No React, no components, no business rules.**

| File | What it does |
|---|---|
| `client.ts` | fetch wrapper, envelope unwrapping, `ApiError`, CSRF |
| `endpoints/` | Typed request functions, one file per backend domain |

**May not import:** `surfaces/`, `domains/`, `design-system/`.

## The envelope

Every backend reply looks like this:

```
success -> { success: true,  message, data }
failure -> { success: false, message, errors: [], code? }
```

`client.ts` unwraps it, so callers get `data` directly and nothing above this
layer knows the envelope exists. Failures become `ApiError`, carrying the
backend message and a stable `code` such as `EMAIL_NOT_VERIFIED` — branch on
the code, never on the message text.

## Why there is no Authorization header

The mobile app holds a JWT and sends `Authorization: Bearer`. **A browser
must not.** Anything JavaScript can read — localStorage, sessionStorage, a
module variable — is readable by any XSS on the page, and a stolen supplier
token is a stolen catalogue.

So the portal authenticates with an httpOnly cookie that JavaScript cannot
read at all. That is why `client.ts` sends `credentials: "include"` and never
a token: there is no token here to send. The cost is CSRF, which is why every
mutating verb carries `X-CSRF-Token`.

**The backend half does not exist yet.** See `docs/v2/V2_00_ARCHITECTURE_EVOLUTION`
section 2.10.
