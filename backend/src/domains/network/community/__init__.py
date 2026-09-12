"""
The Community feed -- a COMPOSER, not a domain that owns anything.

WHY IT IS ITS OWN DOMAIN (V2_04 Part 5). The feed spans supplier,
business, network and catalogue and belongs to none of them. Putting
it inside any one of those would make that domain import the other
three, which is how a marketplace codebase turns into one module.

IT OWNS NO TABLES. It reads from other domains' repositories and
assembles a list. The only table it will ever own is impression
logging, later, and that is a different concern from composition.

  ─────────────────────────────────────────────────────────────────────
  THE RULE, ENFORCED IN tests/architecture: this service may import
  from domain repositories, and NO DOMAIN MAY IMPORT THIS SERVICE.
  ─────────────────────────────────────────────────────────────────────

A coordinator that gets imported by the thing it coordinates stops
being a coordinator -- the same rule already enforced for
shared/finance and shared/ai, and the reason the boundary test ships
in the same commit as the domain rather than "later".

THE SERVER DECIDES ORDER, NOT THE APP. The feed returns a list of
typed sections and the client renders whatever it is handed. That is
what makes a seasonal promo or a paid placement a server change rather
than an app release -- see the frontend's own community/types.ts,
which states the same contract from the other side.
"""
