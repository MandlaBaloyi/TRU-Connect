# `primitives/`

Single-element building blocks. A primitive does one thing and knows nothing
about TruConnect.

Currently: `Wordmark`, `Field`.

Rules that apply to everything here:

- **Label, never placeholder-as-label.** A placeholder vanishes when someone
  types, which makes review guesswork and is invisible to a screen reader.
- **Errors get `aria-invalid` and `aria-describedby`**, not just red text.
- **Focus must be visible.** Someone on a keyboard has to see where they are.
