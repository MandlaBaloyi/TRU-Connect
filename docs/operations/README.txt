===========================================================================
docs/operations/ — RUNBOOKS
===========================================================================

WHAT LIVES HERE: instructions for RUNNING the platform. What to type,
what the output means, what to do when something is wrong.

WHAT DOES NOT: plans, architecture and decisions. Those are docs/v2/ and
the numbered specs above. A runbook says "type this"; a plan says "here
is why". Mixing them produces a document nobody can act on in a hurry
and nobody can argue with at leisure.

THE TEST FOR WHETHER SOMETHING BELONGS HERE: could a person who has
never read the architecture follow it correctly at 7am?

ONE EXCEPTION, NAMED RATHER THAN SMUGGLED IN: BACKLOG.txt is not a
runbook. It is here because it is operational -- it is the list you
consult when deciding what to do next -- and because the alternative
was a fourth top-level folder holding one file.

  RUNBOOK_CATALOGUE_REVIEW.txt
      Working the product-match review queue from the terminal, until
      the admin control centre exists. Who may approve, what the
      evidence means, and how to decide.

  BACKLOG.txt
      What is outstanding and how urgent, in one place. An INDEX, not
      a plan -- it points at the documents that hold the reasoning.
      Sorted by the only question that matters for ordering: does
      waiting make this cost more?

  RUNBOOK_SUPPLIER_VERIFICATION.txt
      Whether a supplier can be SEEN by businesses at all -- the
      curtain. Approving, revoking, what to check first, and how to
      use it to test the app's banner.

TWO GATES, TWO RUNBOOKS, AND THEY ARE NOT THE SAME QUESTION.
Verification asks WHO THIS SUPPLIER IS. Catalogue review asks WHAT THEY
ARE SELLING. A supplier can be entirely genuine -- real company, real
documents -- and still list something that must not be sold through
this platform. Passing one gate says nothing about the other.

===========================================================================
