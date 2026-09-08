# `tokens/`

Colours, spacing, type scale — the raw design values.

`brand.ts` **mirrors** `frontend/mobile/src/theme/colors.ts` rather than
importing it. A React Native app and a Next app cannot share a module
without extracting a package, and a package is not worth its weight for
nine hex values.

**Change a colour here, change it there too.** Same hand-kept-in-sync
discipline the backend uses for `row_validator.py` and its TypeScript twin.

The same values are declared again as Tailwind theme variables in
`app/globals.css`, so `bg-brand-blue` and `brand.blue` are the same colour.
