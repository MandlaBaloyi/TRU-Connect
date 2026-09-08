# `imports/`

CSV and price-file upload: column mapping, staging, preview, commit.

Empty until the portal is built. **This is the reason the web hub exists** —
it is the one job a phone genuinely cannot do.

Two constraints from the architecture:

**No fixed template.** A supplier with 3,000 rows already has a spreadsheet
with their own column names. Asking them to rename columns loses them at the
door — so we map their headers to ours, not the reverse.

**Upsert, never create-only.** A real supplier sends a price file every week.
The one-time import is the exception; the recurring update is the
relationship. See V2_00 section 2.6.
