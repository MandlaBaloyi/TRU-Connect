# `primitives/`

Single-element building blocks. A primitive does one thing and knows nothing
about TruConnect.

Currently: `Wordmark`, `Field`, `Button`, `Container`, `PageHeading`.

`Button` is exported as a class recipe (`buttonClass(...)`) as much as a
component — half the "buttons" on the marketing site are links (`<Link>`, an
external app-store `<a>`), and a component that renders `<button>` forces
them all to fight it. The recipe keeps the primitive free of `next/link`.

Rules that apply to everything here:

- **Label, never placeholder-as-label.** A placeholder vanishes when someone
  types, which makes review guesswork and is invisible to a screen reader.
- **Errors get `aria-invalid` and `aria-describedby`**, not just red text.
- **Focus must be visible.** Someone on a keyboard has to see where they are.
