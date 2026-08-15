"""
Real concurrency test for ConnectionRequestRepository.create() -- not
a simulation. Uses a threading.Barrier to force every thread to fire
the exact same INSERT at the exact same instant, maximizing the
chance of hitting the real race window between the caller's own
"does this already exist" check and this repository's own commit.

Found by direct code inspection while building a live-server
concurrency test for the "tests" item in this session's own backlog:
create() had no protection against the unique constraint
(uq_connection_requests_business_supplier) firing under genuine
concurrent load -- the constraint itself always prevented a duplicate
ROW, but the SECOND caller to lose that race would have hit an
unhandled IntegrityError (a 500), contradicting the "idempotent"
claim the calling service layer's own docstring made. Fixed directly
in create() (catch, rollback, return the winning row) so every caller
(request_connection, request_connection_to_business,
complete_invitations_for_user) gets the protection automatically.
"""
from __future__ import annotations

import threading

from src.domains.network.connections.repositories.connection_request_repository import ConnectionRequestRepository
from src.domains.network.connections.models.connection_request import ConnectionRequest


def test_concurrent_create_never_raises_and_produces_exactly_one_row(
    app, make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Race Test Co")
    business_id = business.id
    profile_id = profile.id

    thread_count = 12
    barrier = threading.Barrier(thread_count)
    results = []
    errors = []

    def attempt():
        with app.app_context():
            try:
                barrier.wait()  # every thread fires the INSERT at the exact same instant
                row = ConnectionRequestRepository.create(business_id, profile_id)
                results.append(row.id)
            except Exception as e:  # noqa: BLE001 -- intentionally broad, this test's whole point is "did ANYTHING raise"
                errors.append(repr(e))

    threads = [threading.Thread(target=attempt) for _ in range(thread_count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"unhandled exception(s) under real concurrency: {errors}"
    assert len(results) == thread_count
    assert len(set(results)) == 1, "threads disagreed on which row won the race"
    assert ConnectionRequest.query.count() == 1
