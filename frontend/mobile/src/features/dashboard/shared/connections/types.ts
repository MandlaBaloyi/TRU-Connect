/**
 * My Connections — Community tab, both roles. Lives under
 * dashboard/shared/ (not business/ or supplier/) because it genuinely
 * IS one thing, not two role-specific mirrors: the backend serves
 * both roles from the SAME endpoint
 * (GET /supplier-discovery/connections), branching on the caller's
 * own JWT role rather than exposing two separate URLs the way Find
 * Supplier/Find Business or Customer/Supplier Requests do — see that
 * endpoint's own docstring for why. The frontend follows the same
 * shape: one feature, one service, one hook, used by both Community
 * tabs.
 *
 * ACTIVE connections only, regardless of which side originally
 * initiated — a request that's still PENDING or was DECLINED never
 * appears here. Real backend, tested end-to-end (both directions,
 * real Postgres) before this file was written.
 */

export interface ConnectionSummary {
  id: string;
  /** The OTHER party's display name — a supplier's business name
   *  when viewed by a business, or a business's name when viewed by
   *  a supplier. Same field name either way; what it represents
   *  depends entirely on who's asking, which the backend already
   *  resolves — this type doesn't need to know which role it's for. */
  name: string;
  /** The OTHER party's own real profile id — a supplier_profile_id
   *  when viewed by a business, a BusinessProfile.id when viewed by a
   *  supplier. Same "meaning depends on who's asking" pattern as name
   *  above. Null in the rare edge case where the other party's own
   *  profile doesn't exist yet — a row with a null id should render
   *  as non-tappable, never a broken link. NEVER the same as this
   *  object's own `id` above (the connection request's own id, not
   *  useful for routing to a profile). */
  otherPartyId: string | null;
  connectedSince: string | null;
}

/**
 * The "who have I disconnected from" list -- business-only today (no
 * equivalent supplier-side flow exists yet, see
 * connections_routes.py's own list_ended_connections docstring).
 * Deliberately a separate type from ConnectionSummary, not that same
 * type with more optional fields -- the two carry genuinely different
 * information for genuinely different purposes.
 */
export interface EndedConnectionSummary {
  id: string;
  name: string;
  otherPartyId: string | null;
  endedReason: string | null;
  endedDetails: string | null;
  endedAt: string | null;
}

// ---------------------------------------------------------------------------
// BACKEND CONTRACT — REAL and tested end-to-end against real Postgres,
// both roles, before this frontend was written.
// ---------------------------------------------------------------------------

/**
 * GET /api/v1/supplier-discovery/connections
 *     -> { connections: ConnectionSummary[] }
 *     Any authenticated business or supplier — no role_required, the
 *     backend branches on the caller's own JWT role to decide which
 *     side of ConnectionRequest to read from.
 *
 * GET /api/v1/supplier-discovery/connections/ended
 *     -> { connections: EndedConnectionSummary[] }
 *     Business-only.
 */

/** Matches the real backend's own EndConnectionSchema exactly
 *  (connections_schemas.py) -- uppercase, since this codebase's enums
 *  store the Python member NAME on the wire, not the lowercase
 *  .value string. Lives here (not business/find-supplier/, where
 *  endConnection/reportSupplier themselves are called from) because
 *  this shared/connections/ screen (DisconnectedSuppliersScreen.tsx)
 *  needs these same labels too, and shared/ code depending on
 *  business/ would invert the "shared is neutral ground" principle
 *  already established for shared/audit and shared/media. */
export type DisconnectReason = "FOUND_BETTER_SUPPLIER" | "NO_LONGER_NEEDED" | "BAD_EXPERIENCE" | "OTHER";

export const DISCONNECT_REASONS: { value: DisconnectReason; label: string }[] = [
  { value: "FOUND_BETTER_SUPPLIER", label: "Found a better supplier" },
  { value: "NO_LONGER_NEEDED", label: "No longer need this supplier" },
  { value: "BAD_EXPERIENCE", label: "Bad experience" },
  { value: "OTHER", label: "Other" },
];

/** Matches ReportSupplierSchema exactly, same reasoning as
 *  DisconnectReason above. */
export type ReportReason =
  | "FAKE_PRODUCTS"
  | "SUSPECTED_SCAM"
  | "ORDER_NOT_RECEIVED"
  | "INAPPROPRIATE_CONTENT"
  | "OTHER";

export const REPORT_REASONS: { value: ReportReason; label: string }[] = [
  { value: "FAKE_PRODUCTS", label: "Selling fake or counterfeit products" },
  { value: "SUSPECTED_SCAM", label: "Suspected scam" },
  { value: "ORDER_NOT_RECEIVED", label: "Never received what was ordered" },
  { value: "INAPPROPRIATE_CONTENT", label: "Inappropriate content" },
  { value: "OTHER", label: "Other" },
];
