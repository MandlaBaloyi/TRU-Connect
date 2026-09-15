"""
The NAMES of the privileged things a staff account can do.

DECLARED NOW, ENFORCED LATER, and the split is the entire point of
this file. Today there is one admin who can do everything, so a
permissions table would be a system with nothing in it -- a grant
screen, a join table and a migration, all to answer a question that
currently has one answer. That is machinery built ahead of need.

What is NOT premature is the SEAM. Every privileged command already
has to say something about itself; having it say

    require_capability(CATALOGUE_REVIEW)

instead of

    require_admin()

costs nothing today and changes what the code MEANS. The first names
the job. The second names the person, and a codebase full of the
second is how you end up unable to hire a finance admin without
auditing forty call sites to work out which of them assumed "admin"
meant "everything".

THE COST ASYMMETRY IS THE ARGUMENT. Adding a grants table later is a
day's work. Finding every place that quietly assumed full access is
the part that eats a month -- and it is unavoidable if the call sites
never recorded what they actually needed. So: record it now, resolve
it cheaply now, and change ONE function when the second staff role
arrives.

NAMING: "<area>:<verb>", lowercase, no plurals. The area matches the
domain that owns the thing being acted on, so a name is greppable
straight to the code it governs.
"""
from __future__ import annotations

#: Work the product match review queue -- accept or reject a proposed
#: link between a supplier's offer and a catalogue product. Writes a
#: GLOBAL alias, so the blast radius is every supplier on the platform.
CATALOGUE_REVIEW = "catalogue:review"

#: Approve or refuse a supplier's commercial verification: their
#: documents, their photographs, their claim to be a real trading
#: business. NOT BUILT YET -- src/domains/verification/ is empty
#: scaffolding. The name is here because naming it costs nothing and
#: having it already spelled correctly means the verification work
#: never has to invent its own vocabulary.
SUPPLIER_VERIFY = "supplier:verify"

#: Put a supplier on a plan: FREE, PRO, MAX or PARTNER. DELIBERATELY
#: NOT supplier:verify, though the same person holds both today.
#: Deciding a business is real and deciding what they may pay for reach
#: are different jobs, and one day they are different people -- a
#: salesperson who closes a PARTNER agreement has no business opening
#: the verification curtain. Naming them apart costs nothing now and is
#: precisely the thing that is expensive to retrofit.
SUPPLIER_PLAN = "supplier:plan"

#: Create, list and deactivate staff accounts. Deliberately its own
#: capability rather than something every admin implies: the ability to
#: review a catalogue and the ability to MINT SOMEONE WHO CAN is a
#: distinction worth keeping available, even while one person holds
#: both.
ADMIN_MANAGE = "admin:manage"

#: Every capability, with a sentence a human can read. Used when a
#: command has to explain what it is asking for -- an error that says
#: "you may not work the review queue" is actionable; one that says
#: "missing catalogue:review" is a support ticket.
ALL: dict = {
    CATALOGUE_REVIEW: "work the product match review queue",
    SUPPLIER_VERIFY: "approve or refuse supplier verification",
    SUPPLIER_PLAN: "set what a supplier pays for, and their reach",
    ADMIN_MANAGE: "create and manage staff accounts",
}
