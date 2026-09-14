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
  /** The other party's resolved avatar — a supplier's brand/personal
   *  photo when viewed by a business, a business's photo when viewed by
   *  a supplier. Null is the normal case (nobody uploaded one, or it's
   *  not shared); the list falls back to an initials avatar. */
  photoUrl: string | null;
  /** The other party's verification, when they are a SUPPLIER. Null
   *  when a supplier is viewing their business customers -- businesses
   *  are not verified this way, and null must read as "this payload
   *  does not say", never as "not verified".
   *
   *  THIS LIST IS ONE OF THE FEW PLACES IT VARIES. The curtain hides
   *  unverified suppliers from discovery, but leaves established
   *  connections alone on purpose, so a supplier revoked after you
   *  connected still appears here -- without a tick. */
  verificationStatus: string | null;

  /* ---- the relationship ledger (V2_04 2.3) ----------------------------
   * A connection is not a contact; it is a trading relationship, and
   * these are what make the row worth reading. ALL OF THEM ARE EMPTY FOR
   * A FRESH CONNECTION and that is the normal state, not an error —
   * render a plain row, never zeroes and never "overdue".
   * The SERVER decides the order of the list; the client renders as
   * given. See connection_list_service._as_ledger for why. */

  /** Orders that count toward a rhythm — carts, declined and cancelled
   *  are excluded, so this is not "how many times we talked". */
  orderCount: number;
  lastOrderAt: string | null;
  /** Null until there is enough history to call anything typical: one
   *  order is not a pattern. */
  typicalGapDays: number | null;
  /** Silent for noticeably longer than this pair's own usual gap —
   *  a ratio, not a fixed number of days, so a weekly buyer and a
   *  monthly one are both judged against themselves. */
  isOverdue: boolean;
  /** HOW MANY are still in flight. Three orders where one is done
   *  and two are waiting is a different row from one waiting order,
   *  and "Order waiting" cannot tell them apart. */
  openOrderCount: number;
  /** The OLDEST of them — the one that has been waiting longest, so
   *  the one somebody needs to act on. Null is the common case. */
  openOrder: { id: string; status: string; submittedAt: string | null } | null;
  /** The PERSON behind the business, shown under the business name in
   *  the connection row. Null whenever no person name exists — owner
   *  name is optional at supplier sign-up — in which case the row shows
   *  one line, never a blank second one. */
  ownerName: string | null;
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
