# `types/`

TypeScript types shared across more than one layer.

Most types should NOT live here. A type describing an offer belongs in
`domains/catalogue/types.ts`; a type describing a Button's props belongs
beside the Button. This folder is for the genuinely cross-cutting few.

An empty folder here is a good sign.
