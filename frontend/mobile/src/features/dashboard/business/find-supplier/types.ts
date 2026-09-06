/**
 * Find Supplier — Phase 1 of the TRU Connect network engine (per the
 * FILE2.txt build plan: "DO NOT BUILD PHASE 2 YET... FIRST TARGET:
 * SUPPLIER DISCOVERY"). This is a search, not a browse — TRU Connect
 * digitises an EXISTING relationship, it doesn't help a business
 * discover suppliers it's never worked with (file.txt §4: "should NOT
 * expose everybody").
 *
 * FRONTEND-ONLY PHASE, mocked (services/supplierSearchService.ts).
 * These types are the shape the real backend contract will return —
 * see the bottom of this file for the documented future endpoint —
 * so wiring the backend later is a service-layer swap, same
 * discipline as my-account/types.ts.
 *
 * PRIVACY BY CONSTRUCTION: SupplierSearchResult and
 * SupplierProfilePreview are deliberately narrow. There is no field
 * on either type that could carry a supplier's full phone number,
 * full email, or exact address — only enough to let the business
 * recognise "yes, that's my supplier" (file.txt §4's own framing).
 *
 * SEARCH IS NAME/BUSINESS-NAME ONLY -- phone/email exact-match search
 * was REMOVED (backend: connections_service.py's own _dispatch_search
 * docstring has the full reasoning). Even with the matched identifier
 * masked, exact-match phone/email search let someone probe arbitrary
 * numbers/addresses one at a time to learn who's registered — a real
 * enumeration vector, not a theoretical one. MatchedField/
 * matchedField/maskedMatchedIdentifier are GONE from this file
 * entirely, not just unused — once name is the only match kind,
 * carrying fields whose value never varies is dead weight in both the
 * type and every consumer that has to keep it in sync for no reason.
 */

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

export interface SupplierSearchQuery {
  /** Business name only now — see file header. The business types a
   *  name (or the start of one); there's no phone/email branch to
   *  route to anymore. */
  query: string;
}

// ---------------------------------------------------------------------------
// Results — narrow by design, see file header
// ---------------------------------------------------------------------------

// Lowercase, matching auth's own VerificationStatus type exactly
// (src/features/auth/types.ts) and the real backend's actual JSON
// output (SupplierProfile.to_search_result_dict uses
// self.verification_status.value, which is lowercase) — confirmed via
// a real HTTP response during backend testing, not assumed.
export type SupplierVerificationStatus = "verified" | "unverified" | "pending";

export interface SupplierSearchResult {
  id: string;
  businessName: string;
  /** General category only, e.g. "Wholesale beverages" — never a
   *  full stored profile. */
  category: string | null;
  /** Suburb/city only, never a street address. */
  location: string | null;
  verificationStatus: SupplierVerificationStatus;
  /** Resolved server-side, respecting the supplier's own
   *  photo_visibility/visible_image_source settings — genuinely null
   *  unless they've actively chosen to show something AND the
   *  visibility rule allows it for THIS viewer specifically (their
   *  own EVERYONE choice, or a genuinely ACTIVE connection under
   *  CONNECTIONS). Never assume presence; always render the
   *  fallback/initials state when null. */
  photoUrl: string | null;
}

// ---------------------------------------------------------------------------
// Supplier profile preview — one level deeper than a result card, still
// narrow. This is NOT the supplier's full stored profile (that's a
// later, relationship-gated concern) — just enough to decide whether
// to request a connection.
// ---------------------------------------------------------------------------

export interface SupplierProfilePreview {
  id: string;
  businessName: string;
  category: string | null;
  location: string | null;
  verificationStatus: SupplierVerificationStatus;
  /** Year only, deliberately not an exact date — file.txt's own
   *  privacy framing applied consistently: enough to build trust,
   *  not enough to fingerprint. */
  memberSinceYear: number | null;
  /** Short, supplier-authored description — optional, may be null if
   *  the supplier hasn't written one. */
  description: string | null;
  connectionStatus: ConnectionStatus;
  /** Same resolution rule as the search result's own photoUrl —
   *  see that field's doc comment. */
  photoUrl: string | null;
  /** Real — how many products this supplier has actually listed.
   *  Drives the profile screen's "View Products" entry point: an
   *  honest empty state when 0, a real (if minimal) list otherwise. */
  productCount: number;
  /** Null unless there's an ACTIVE connection AND the supplier has
   *  opted into share_contact_details -- same double gate, same
   *  SupplierContactDetails shape as the catalog's own contact block
   *  (see ContactSupplierSheet.tsx). Added specifically so a business
   *  viewing a CONFIRMED order (which they can no longer self-cancel)
   *  has a real way to reach the supplier directly. */
  contact: SupplierContactDetails | null;
}

// ---------------------------------------------------------------------------
// Connection request — the future supplier_customer_relationship state
// machine (file.txt §Phase 2/3). Modelled here in full even though
// Phase 1 only ever produces NOT_REQUESTED -> PENDING; the type exists
// so this screen doesn't need to change shape once Approve/Decline
// (Phase 3) is built — it'll just start receiving ACTIVE/DECLINED too.
// ---------------------------------------------------------------------------

export type ConnectionStatus = "NOT_REQUESTED" | "PENDING" | "ACTIVE" | "DECLINED" | "SUSPENDED" | "TERMINATED";

// ---------------------------------------------------------------------------
// Supplier Invitation — file.txt Phase 2 (the "supplier isn't on
// TruConnect yet" branch). Lives in this same feature file, not a
// separate one — it's the other entry point into the exact same
// relationship Request Connection above creates, just reached without
// a search step. Backend: network/supplier_discovery's
// SupplierInvitation, POST /supplier-discovery/invitations.
// ---------------------------------------------------------------------------

export interface InviteSupplierResult {
  status: "SENT";
}

// ---------------------------------------------------------------------------
// BACKEND CONTRACT — all of the below are REAL and tested (not a future
// plan): network/supplier_discovery, verified end-to-end against real
// Postgres, including the full invitation lifecycle (invite -> register
// with ticket -> verify -> auto-created PENDING relationship -> approve).
// ---------------------------------------------------------------------------

/**
 * GET  /api/v1/supplier-discovery/search?q=...
 *      -> { results: SupplierSearchResult[] }
 *      Rate-limited per business_id. NAME/BUSINESS-NAME PREFIX MATCH
 *      ONLY (phone/email exact-match search was removed — see file
 *      header). Never a fuzzy "everyone whose name contains this"
 *      scan (file.txt §4).
 *
 * GET  /api/v1/supplier-discovery/suppliers/{id}
 *      -> SupplierProfilePreview
 *      Same privacy narrowing as search results.
 *
 * POST /api/v1/supplier-discovery/suppliers/{id}/connection-requests
 *      -> { connectionStatus: "PENDING" }
 *      business_id from the JWT identity, never the request body.
 *
 * POST /api/v1/supplier-discovery/invitations
 *      body: { email: string }
 *      -> { status: "SENT" }
 *      Business-only, rate-limited. Sends a real, expiring, single-use
 *      ticket by email. When the invited person later registers with
 *      that ticket (auth/register's optional invitationTicket field)
 *      and verifies their email, the same PENDING relationship this
 *      screen's own Request Connection produces gets created
 *      automatically — no search step needed on either side.
 *
 * GET  /api/v1/supplier-discovery/invitations/validate?ticket=...
 *      -> { valid: boolean }
 *      Deliberately UNAUTHENTICATED — lets a registration screen
 *      reached via a deep link say "this invite has expired" before
 *      the person fills in a form.
 */

/**
 * The minimal Catalogue slice — real, tested, deliberately lean (see
 * backend Product model's own docstring: no price/description/images
 * yet). Only name exists right now; this type gets richer once
 * Catalogue itself is properly built, not before.
 */
export interface SupplierProduct {
  id: string;
  name: string;
  /** All genuinely already sent by the real backend (see
   *  connections_service.py's own list_supplier_products) -- the
   *  frontend type simply never captured them until the My
   *  Connections/search UI review found this. */
  category: string;
  priceCents: number;
  /** The "was RX" comparison price for a sale -- null when the
   *  supplier isn't running one. Feeds the same "X% OFF" badge
   *  (products/algorithms/discount.ts) the supplier sees on their own
   *  product screens -- a real discount is real regardless of who's
   *  looking at it. */
  compareAtPriceCents: number | null;
  sellingUnit: string;
  /** A real, direct answer to "can I actually order this right now" --
   *  never the exact quantity. Computed server-side from the
   *  supplier's real Inventory row (available = on hand - reserved),
   *  and treats a product with no inventory row at all as out of
   *  stock, not an error. */
  inStock: boolean;
  images: string[];
}

/**
 * The real response shape for the catalogue list -- supplierName sits
 * at the top level (same value for every product, so the backend
 * deliberately doesn't repeat it into each one). This is the actual
 * "certainty" fix applied one screen earlier than the product detail
 * screen: a business browsing the whole catalogue sees whose it is
 * before ever tapping into one specific product.
 *
 * contact is the same gated data (SupplierContactDetails, or null)
 * SupplierProductDetail already carries -- added here too so
 * "Contact Supplier" works from the catalogue's own 3-dot menu,
 * without a business needing to first pick one specific product.
 */
export interface SupplierProductsCatalog {
  supplierName: string;
  contact: SupplierContactDetails | null;
  page: number;
  totalPages: number;
  totalCount: number;
  products: SupplierProduct[];
}

/**
 * The real request shape for GET .../products -- page/limit/sort/
 * category are now genuinely applied server-side (see
 * connections_service.py's own list_supplier_products docstring on
 * why: once results are paginated, a client-side sort/filter could
 * only ever see whatever's on the current page, silently missing real
 * matches sitting on other pages). limit is capped server-side
 * regardless of what's requested here -- passing a large number
 * doesn't bypass that.
 */
export interface SupplierProductsQuery {
  page?: number;
  limit?: number;
  sort?: string;
  category?: string | null;
}

/**
 * A supplier's real contact channels -- null (the WHOLE object, not
 * just individual fields) whenever EITHER the requesting business
 * isn't actively connected OR the supplier hasn't opted into sharing.
 * Resolved entirely server-side (see connections_service.py's own
 * get_supplier_product docstring) -- this type never carries a
 * "shouldShow" flag alongside the data, because the data's own
 * presence already IS the permission: if it's here, it's meant to be
 * shown.
 */
export interface SupplierContactDetails {
  whatsappNumber: string | null;
  email: string | null;
  tiktokHandle: string | null;
}

/**
 * One level deeper than SupplierProduct -- everything a business would
 * want before deciding to order: description, and the product's own
 * code (shown to businesses when they order, per Product.productCode's
 * own backend docstring). NOT sku -- that's the supplier's own
 * internal tracking label, not meaningful to a business browsing the
 * catalogue.
 *
 * supplierName and contact are the real "certainty" fix this whole
 * feature exists for -- see connections_service.py's own
 * get_supplier_product docstring for the full reasoning on why
 * contact is gated the way it is.
 */
export interface SupplierProductDetail {
  id: string;
  name: string;
  supplierName: string;
  contact: SupplierContactDetails | null;
  category: string;
  priceCents: number;
  compareAtPriceCents: number | null;
  sellingUnit: string;
  /** Same real, direct meaning as SupplierProduct's own inStock. */
  inStock: boolean;
  description: string | null;
  productCode: string;
  images: string[];
}

/**
 * GET /api/v1/supplier-discovery/suppliers/{id}/products
 *     -> SupplierProductsCatalog
 *     Business-only. Viewable regardless of connection status —
 *     browsing stays open; only ORDERING is gated (a separate,
 *     not-yet-built concern), matching this session's own
 *     architecture-review decision.
 *
 * GET /api/v1/supplier-discovery/suppliers/{id}/products/{productId}
 *     -> SupplierProductDetail
 *     Same visibility rule as the list above. 404 (PRODUCT_NOT_FOUND)
 *     for a genuinely nonexistent product, one belonging to a
 *     different supplier than the URL says, OR an archived one — all
 *     three deliberately indistinguishable from the response, same
 *     IDOR-safety reasoning as SUPPLIER_NOT_FOUND elsewhere in this
 *     domain.
 */

/** DisconnectReason/ReportReason and their option lists now live in
 *  shared/connections/types.ts, not here -- moved there after a real
 *  backward-dependency was caught: DisconnectedSuppliersScreen.tsx
 *  (a shared/ screen) needed these same labels to display each
 *  disconnection's reason, and shared/ code depending on
 *  business/find-supplier/ would invert the same "shared is neutral
 *  ground" principle already established for shared/audit and
 *  shared/media earlier in this project. Re-exported here so every
 *  existing import in this feature (httpSupplierSearchService.ts,
 *  mockSupplierSearchService.ts, and this feature's own components)
 *  keeps working unchanged. */
export type { DisconnectReason, ReportReason } from "../../shared/connections/types";
export { DISCONNECT_REASONS, REPORT_REASONS } from "../../shared/connections/types";
