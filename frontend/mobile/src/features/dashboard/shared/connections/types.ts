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
  connectedSince: string | null;
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
 */
