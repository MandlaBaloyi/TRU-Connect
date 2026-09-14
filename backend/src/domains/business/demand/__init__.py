"""
THE DEMAND ENGINE -- a model of a SHOP, not of a shelf.

It answers one question: WHAT DOES THIS SHOP NEED? The answer is
categories and, later, catalogue products -- never a supplier.

WHY IT LIVES UNDER business/. Its path says whose model it is. It is
not a network concern (it describes one shop, not a relationship) and
not a catalogue concern (the catalogue describes things that exist, this
describes what somebody wants).

THE INVARIANT: delete every supplier on the platform and nothing here
changes. tests/architecture/test_demand_independence.py enforces it,
because the moment supply can reach into the model, "favour this
partner" becomes a one-line change somebody makes on a busy week.

THREE LAYERS (docs/v2/V2_15 Book Three Part 2):

    DECLARED   what they told us. Available on day one, and a
               HYPOTHESIS. This is all Phase 0 uses.
    OBSERVED   what they actually did. EVIDENCE, and slow to arrive.
    DERIVED    computed from both, and the ONLY layer the feed reads.

Phase 0 is deliberately declared-only: it proves that declaration beats
cold start before a single table is added for observation.
"""
