# `auth/`

Sign in, sign up, verification, session.

**`services/authApi.ts` deliberately throws instead of submitting.** The
forms are real and validate, but the transport does not exist yet — the
backend needs cookie sessions and CSRF first (V2_00 section 2.10).

A form that appears to log you in and does not is worse than one that admits
it is not connected.

**There is no business sign-in and there never will be.** Businesses have no
web surface; if one lands on the sign-in page they have taken a wrong turn,
and the page says so rather than letting them try credentials that cannot work.
