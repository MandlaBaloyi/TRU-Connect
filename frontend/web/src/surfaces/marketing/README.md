# `marketing/`

The public site: header, footer, and the landing and supplier pages.

**One audience wide, deliberately.** Every call to action resolves to exactly
two places: get the app, or sign in as a supplier. There is no third door,
because there is no third thing a visitor can usefully do.

Businesses have no web surface at all. Their phone is with them all day and
their problem does not require a desk — see V2_00 section 2.9.

## Rules for pages here

- **Statically generated.** These pages exist to be found by someone who has
  never heard of TruConnect. Nothing here may require a signed-in user.
- **Imagery comes from Cloudinary**, not `public/` — so it can change without
  a deploy and be transformed per device. Someone is opening this on mobile
  data.
- **Claim only what exists.** A supplier who signs up for a promised feature
  and does not find it is worse than one who never heard about it.
