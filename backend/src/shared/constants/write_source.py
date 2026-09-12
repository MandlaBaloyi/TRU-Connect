"""
WHICH CHANNEL wrote a row -- typed in the app, imported from a file,
or pushed by a machine.

WHY THIS EXISTS BEFORE ANYTHING NEEDS IT (V2_13 §3.3). A supplier
edits a price in the app at 09:00. Their ERP pushes the old price at
09:05. Which is correct?

Today that question has no answer, because a price is a value with no
memory of where it came from. At tier 3 and above the ERP is usually
authoritative and the app is usually a convenience -- but "usually" is
a policy, and a policy needs a field to act on. Without one the only
options are to let the last write win (silently reverting deliberate
human edits) or to freeze app editing for integrated suppliers (a
worse product).

  ─────────────────────────────────────────────────────────────────────
  A COLUMN ADDED LATER STARTS NULL FOR EVERY EXISTING ROW, and no
  analysis recovers where a number came from two years ago.
  ─────────────────────────────────────────────────────────────────────

That asymmetry is the whole argument for adding it now rather than
when the first ERP arrives. It is also useful immediately and on its
own terms: "how many of this supplier's prices were typed by hand
versus imported?" is a question worth answering today.

DELIBERATELY THE CHANNEL, NOT THE PERSON. Which SYSTEM wrote this is
what decides a conflict between two sources of truth; which HUMAN did
is a different question, and the audit trail already answers it. A
column that tried to be both would be used for neither.

LIVES IN shared/ because it is vocabulary with no dependencies --
supplier offers and inventory use it today, and a price history or an
order write would use the same three words rather than inventing
their own.
"""
from __future__ import annotations

import enum


class WriteSource(str, enum.Enum):
    #: A person, in the mobile app or the web portal. The default, and
    #: the only value that existed implicitly before this enum did.
    APP = "APP"

    #: A bulk file the supplier uploaded -- see supplier/bulk_import.
    #: Distinct from APP because a spreadsheet is a snapshot of what
    #: some OTHER system believed, often hours old by the time it is
    #: uploaded, and that staleness matters when resolving a conflict.
    IMPORT = "IMPORT"

    #: A machine, authenticated by API key (V2_13 tier 3). Nothing
    #: writes this yet -- the inbound API exists, and the day an ERP
    #: uses it this is the value that lets us say "their system is
    #: authoritative, ours is a cache" rather than guessing.
    API = "API"
