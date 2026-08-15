/**
 * Supplier Requests — the reverse direction of Customer Requests
 * (supplier/customer-requests/types.ts), for businesses. A business
 * sees suppliers that requested a connection (Find Business's own
 * "Request Connection" action, supplier side) and can Approve or
 * Decline. Real backend, tested end-to-end (network/supplier_discovery's
 * ConnectionRequest.initiated_by_role is what makes this the correct
 * mirror rather than a duplicate concept — see that model's own
 * docstring).
 *
 * PRIVACY, same principle as Customer Requests: enough for the
 * business to recognise "yes, that's my supplier", never the
 * supplier's full stored record.
 */

export type ConnectionRequestStatus = "PENDING" | "ACTIVE" | "DECLINED";

export interface SupplierRequestSummary {
  id: string;
  businessName: string;
  requestedAt: string;
  status: ConnectionRequestStatus;
}

export interface SupplierRequestDetail {
  id: string;
  businessName: string;
  ownerName: string | null;
  category: string | null;
  location: string | null;
  maskedPhone: string | null;
  maskedEmail: string | null;
  requestedAt: string;
  status: ConnectionRequestStatus;
}

// ---------------------------------------------------------------------------
// BACKEND CONTRACT — REAL and tested end-to-end against real Postgres.
// ---------------------------------------------------------------------------

/**
 * GET  /api/v1/supplier-discovery/supplier-requests
 *      -> { requests: SupplierRequestSummary[] }
 *      Business-only (role_required("business")) — the mirror image
 *      of Find Business's supplier-only routes.
 *
 * GET  /api/v1/supplier-discovery/supplier-requests/{id}
 *      -> SupplierRequestDetail
 *
 * POST /api/v1/supplier-discovery/supplier-requests/{id}/approve
 *      -> { status: "ACTIVE" }
 *
 * POST /api/v1/supplier-discovery/supplier-requests/{id}/decline
 *      -> { status: "DECLINED" }
 *
 * business_id (whose requests these are) comes from the JWT identity,
 * never the request body/URL.
 */
