/**
 * Find Business — the reverse direction of Find Supplier
 * (business/find-supplier/types.ts), for suppliers. Same privacy-by-
 * construction discipline: BusinessSearchResult/BusinessProfilePreview
 * are deliberately narrow, mirroring the exact field set the real
 * backend's BusinessProfile.to_search_result_dict/to_profile_preview_dict
 * already return — verified directly against those methods, not
 * assumed, which is also why there's NO verificationStatus field here:
 * BusinessProfile doesn't have one (unlike SupplierProfile's), so this
 * type doesn't invent a field the backend can't actually populate.
 *
 * SEARCH IS NAME/BUSINESS-NAME ONLY -- phone/email exact-match search
 * was REMOVED, mirroring find-supplier/types.ts's own identical
 * change; see that file's header for the full enumeration-vector
 * reasoning. matchedField/maskedMatchedIdentifier are GONE from this
 * file entirely, not just unused.
 *
 * REAL BACKEND, not mocked-first this round — network/supplier_discovery
 * was extended and tested end-to-end (both directions, real Postgres)
 * before this frontend was written. Still ships with a mock
 * implementation alongside the real one, same mock/http/boundary split
 * as every other feature in this app, so USE_MOCK_API stays a
 * consistent, app-wide toggle rather than working for some features
 * and not others.
 */

export interface BusinessSearchQuery {
  query: string;
}

export interface BusinessSearchResult {
  id: string;
  businessName: string;
  category: string | null;
  location: string | null;
  /** Resolved server-side — see find-supplier/types.ts's own
   *  SupplierSearchResult.photoUrl doc comment for the full
   *  reasoning; identical rule, other direction. */
  photoUrl: string | null;
}

export interface BusinessProfilePreview {
  id: string;
  businessName: string;
  category: string | null;
  location: string | null;
  memberSinceYear: number | null;
  description: string | null;
  connectionStatus: ConnectionStatus;
  photoUrl: string | null;
}

// Reused as-is — the exact same relationship state machine Find
// Supplier's own ConnectionStatus models, since this is genuinely the
// same underlying ConnectionRequest row, just reached from the other
// side (see network/supplier_discovery's own initiated_by_role note).
export type ConnectionStatus = "NOT_REQUESTED" | "PENDING" | "ACTIVE" | "DECLINED" | "SUSPENDED" | "TERMINATED";

export interface InviteBusinessResult {
  status: "SENT";
}

// ---------------------------------------------------------------------------
// BACKEND CONTRACT — REAL and tested end-to-end against real Postgres,
// both directions, including the full reverse-invitation lifecycle
// (supplier invites -> business registers with ticket -> verifies ->
// auto-created PENDING relationship -> business approves).
// ---------------------------------------------------------------------------

/**
 * GET  /api/v1/supplier-discovery/businesses/search?q=...
 *      -> { results: BusinessSearchResult[] }
 *      Supplier-only, rate-limited. NAME/BUSINESS-NAME PREFIX MATCH
 *      ONLY, mirroring Find Supplier's own search exactly.
 *
 * GET  /api/v1/supplier-discovery/businesses/{id}
 *      -> BusinessProfilePreview
 *
 * POST /api/v1/supplier-discovery/businesses/{id}/connection-requests
 *      -> { connectionStatus: "PENDING" }
 *      supplier_id from the JWT identity, never the request body.
 *
 * POST /api/v1/supplier-discovery/business-invitations
 *      body: { email: string }
 *      -> { status: "SENT" }
 *      Supplier-only, rate-limited.
 *
 * GET  /api/v1/supplier-discovery/invitations/validate?ticket=...
 *      -> { valid: boolean }
 *      Same shared endpoint Find Supplier's own invitation flow uses
 *      — one validation endpoint serves both directions.
 */
