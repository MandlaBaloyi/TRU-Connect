# `marketing/`

The public site: header, footer, and the page bodies behind every route
in `app/(marketing)/` — `Landing`, `Suppliers`, `About`, `Contact`, and
`LegalDocument` (Terms and Privacy). The route files in `app/` only wire a
URL to one of these; all copy and structure live here.

`imagery.ts` + `CloudinaryImage` are the image pipeline: a named catalogue
of Cloudinary public ids, resolved through the pure builder in
`@/lib/cloudinary`. The public ids are placeholders on the
`truconnect/marketing/<name>` convention until `NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME`
is set and the assets exist — until then every image slot renders a
brand panel of the right shape, so the layout is correct either way.

`legalContent.ts` is ported verbatim from the mobile app's
`src/content/legal/` (which is React Native and cannot be imported). If
that text changes, change it here too.

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
