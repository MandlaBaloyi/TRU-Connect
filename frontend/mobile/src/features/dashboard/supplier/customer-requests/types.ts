/**
 * Customer Requests — file.txt Phase 3 / FILE2.txt "PHASE 3 — SUPPLIER
 * APPROVAL". A supplier sees businesses that requested a connection
 * (Find Supplier's own "Request Connection" action, business side)
 * and can Approve or Decline. Approving is what actually sets
 * relationship.status = ACTIVE, which is what unlocks ordering later
 * — this screen is the other half of what Find Supplier already
 * built and shipped.
 *
 * FRONTEND-ONLY PHASE, mocked (services/customerRequestsService.ts) —
 * same discipline as find-supplier/types.ts: these types are the
 * shape the real backend already returns in places it overlaps (the
 * connection-request status enum matches
 * network/supplier_discovery/models/connection_request.py's
 * ConnectionRequestStatus exactly, since this is genuinely the same
 * underlying row, just read from the supplier's side of it).
 *
 * PRIVACY, same principle as find-supplier/types.ts applied to the
 * other direction: enough for the supplier to recognise "yes, that's
 * my customer", never the business's full stored record.
 */

export type ConnectionRequestStatus = "PENDING" | "ACTIVE" | "DECLINED";

export interface CustomerRequestSummary {
  /** The connection request's own id — never the business's raw
   *  account id, same reasoning as SupplierSearchResult using the
   *  supplier PROFILE id, not the supplier's account id. */
  id: string;
  businessName: string;
  requestedAt: string;
  status: ConnectionRequestStatus;
}

export interface CustomerRequestDetail {
  id: string;
  businessName: string;
  ownerName: string | null;
  category: string | null;
  location: string | null;
  /** Masked, same convention as find-supplier's own maskedMatchedIdentifier
   *  — enough to confirm identity, never the full stored value. */
  maskedPhone: string | null;
  maskedEmail: string | null;
  requestedAt: string;
  status: ConnectionRequestStatus;
}

// ---------------------------------------------------------------------------
// FUTURE BACKEND CONTRACT — mirrors network/supplier_discovery's own
// documented contract (find-supplier/types.ts), since this is the
// supplier-side view of the exact same ConnectionRequest rows.
// ---------------------------------------------------------------------------

/**
 * GET  /api/v1/supplier-discovery/customer-requests
 *      -> { requests: CustomerRequestSummary[] }
 *      Supplier-only (role_required("supplier")) — the mirror image
 *      of Find Supplier's business-only routes.
 *
 * GET  /api/v1/supplier-discovery/customer-requests/{id}
 *      -> CustomerRequestDetail
 *
 * POST /api/v1/supplier-discovery/customer-requests/{id}/approve
 *      -> { status: "ACTIVE" }
 *
 * POST /api/v1/supplier-discovery/customer-requests/{id}/decline
 *      -> { status: "DECLINED" }
 *
 * supplier_id (whose requests these are) comes from the JWT identity,
 * never the request body/URL — same rule as every other route in this
 * codebase.
 */
