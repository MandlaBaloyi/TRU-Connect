# `lib/`

Pure helpers: formatting, currency, dates. No React, no network, no state.

**May not import anything else in `src/`.** If a helper needs a domain type
it is not a helper, it belongs in that domain.

The test: could this be published as a standalone package and still make
sense? If not, it goes somewhere else.
