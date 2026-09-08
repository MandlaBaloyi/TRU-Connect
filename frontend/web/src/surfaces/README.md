# `surfaces/` — layer 3

Screens and shells, organised by **audience**. This is where audiences split,
because presentation is the thing that actually differs between them.

**May import:** `domains/`, `design-system/`, `api/`, `lib/`, `config/`.
**May not import:** another surface.

That last rule has teeth. If the portal and the marketing site genuinely need
the same thing, it belongs in `design-system/` or `domains/` — and having to
move it is the point, not an inconvenience.

| Surface | Audience | Auth |
|---|---|---|
| `marketing/` | Anyone. Public, indexed by search engines. | none |
| `portal/` | Suppliers. | cookie session + role |
| `admin/` | TruConnect staff. Deliberately absent for now. | cookie session + role |

Admin is the whole control centre and is a lot of work. It arrives once the
ecosystem is complete — and costs nothing to defer, because it will compose
domains that already exist rather than needing new ones.
