"""
Reconciliation ALGORITHMS -- pure matching, balancing, variance.

NOT the reconciliation DOMAIN. The split mirrors shared.audit vs
security.audit exactly:

    shared/finance/reconciliation/    the maths: do these two sets of
                                      numbers agree, and by how much?
    domains/platform/reconciliation/  the workflow: cases, approvals,
                                      investigations, dashboards, jobs

Example: Wallet says paid R500, bank says received R500. This package
answers "difference = 0, matched". The DOMAIN decides what to do about
that -- mark reconciled, log audit, close the case.

NOT IMPLEMENTED YET -- there is nothing to reconcile until real money
movement exists (Wallet/Settlement). The package exists so the boundary
is established before the first implementation lands, not after.
"""
