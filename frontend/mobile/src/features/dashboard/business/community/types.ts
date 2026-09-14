/**
 * The Community feed contract.
 *
 * THE ONE ARCHITECTURAL DECISION THIS FILE EXISTS TO ENFORCE: the
 * SERVER decides which sections appear and in what order. The app
 * renders whatever list it is handed and knows nothing about the
 * ordering rules.
 *
 * That is not a style preference, it is what makes the commercial side
 * of this product possible. When a wholesaler joins and wants their
 * range placed above the fold, or a seasonal promo needs to run for a
 * fortnight, that is a server change — no app release, no store
 * review, no waiting for users to update. Hardcoding "rail 1 is
 * buy-it-again, rail 2 is recommended" would make every one of those
 * conversations a two-week release cycle.
 *
 * UNKNOWN SECTION TYPES RENDER NOTHING, DELIBERATELY (see
 * FeedSection.tsx's default case). The server must be free to ship a
 * new section type before every installed app understands it —
 * otherwise the contract is only as flexible as the oldest build in
 * the wild, which defeats the point above.
 *
 * NOTHING HERE IS INVENTED FOR DECORATION. Every field is either
 * already returned by an existing endpoint or is a real, named gap
 * with a plan behind it (see NOT-YET-REAL below). A feed that displays
 * numbers the platform cannot stand behind would undo the same
 * honesty the track record and payment-status work were built on.
 */

// ---------------------------------------------------------------------------
// Items
// ---------------------------------------------------------------------------

export interface FeedSupplier {
  id: string;
  businessName: string;
  /** Brand assets — public, ungated, same as the brand profile uses. */
  businessImageUrl: string | null;
  coverImageUrl: string | null;
  category: string | null;
  /** Suburb/city only, never a street address. */
  location: string | null;
  verificationStatus: string | null;

  /** THE META LINE, and every field in it is real.
   *
   *  DELIBERATELY NOT a star rating or a delivery-time estimate, which
   *  is what the apps this borrows its shape from lead with. TRU
   *  Connect has neither: reviews were rejected outright (nothing here
   *  can be gamed the way a review score invites), and nothing records
   *  delivery, so a "25 min" badge would be invented. What is below is
   *  what the platform can actually stand behind. */
  offersDelivery: boolean | null;
  minimumOrderCents: number | null;
  connectedBusinessCount: number;
  /** Null unless the supplier opted in — the gate is the field's
   *  absence, so a screen that forgets to check a flag can't leak it. */
  lastActiveAt: string | null;
  /** Whether THIS business already has an active connection. Drives
   *  "Connected" vs "Connect" on the card without a second request. */
  isConnected: boolean;

  /** NOT YET REAL — null from the http service until the feed endpoint
   *  computes it (phase 4). Both sides have coordinates already
   *  (BusinessProfile.latitude/longitude and the supplier's collection
   *  address), so this is a query away rather than a new data model.
   *  The mock returns it so the UI is designed for it now; every
   *  consumer must render correctly when it is null. */
  distanceKm: number | null;
}

export interface FeedProduct {
  id: string;
  supplierId: string;
  supplierName: string;
  name: string;
  imageUrl: string | null;
  priceCents: number;
  /** Struck-through original — null when not discounted. */
  compareAtPriceCents: number | null;
  /** "each", "case of 12" — real, from Product.unit_quantity/unit_measure. */
  unitLabel: string | null;
  inStock: boolean;
  /** How many DISTINCT businesses have bought this. null when nobody
   *  has yet — never 0, because "0 businesses bought this" is true,
   *  useless, and reads as a warning. */
  buyerCount: number | null;
  /** The sentence, built SERVER-SIDE so the wording is one decision:
   *  the feed and the catalogue browse both render product cards, and
   *  a phrase duplicated across them disagrees with itself within a
   *  release. null whenever buyerCount is. */
  buyerLabel: string | null;
}

export interface FeedCategory {
  /** Matches ProductCategory on the backend, so a chip can filter for real. */
  value: string;
  label: string;
  /** Lucide icon name, resolved by the chip. Server-chosen so a new
   *  category doesn't need an app release to get an icon. */
  icon: string | null;
}

export interface FeedPromo {
  title: string;
  body: string | null;
  imageUrl: string | null;
  /** Where tapping it goes. A route string, validated by the app
   *  before navigating — never an arbitrary URL from the server. */
  href: string | null;
}

// ---------------------------------------------------------------------------
// Sections
// ---------------------------------------------------------------------------

interface SectionBase {
  /** Stable across refreshes — used as the React key and, later, as
   *  the impression key when this feed is measured. */
  id: string;
}

export type FeedSection =
  | (SectionBase & { type: "CATEGORY_CHIPS"; categories: FeedCategory[] })
  | (SectionBase & { type: "SUPPLIER_AVATARS"; title: string; suppliers: FeedSupplier[] })
  | (SectionBase & {
      type: "SUPPLIER_RAIL";
      title: string;
      subtitle?: string | null;
      suppliers: FeedSupplier[];
      seeAllHref?: string | null;
    })
  | (SectionBase & {
      type: "PRODUCT_RAIL";
      title: string;
      subtitle?: string | null;
      products: FeedProduct[];
      seeAllHref?: string | null;
    })
  | (SectionBase & { type: "PROMO"; promo: FeedPromo })
  | (SectionBase & {
      /** BUILT BEFORE IT IS SOLD, on purpose. Nothing fills this today.
       *  It exists so the paid-placement design is proven and shipped
       *  in the app BEFORE the first wholesaler conversation, rather
       *  than being retrofitted under deadline once one is signed. The
       *  label is server-supplied ("Sponsored", "Featured partner") so
       *  the wording can follow whatever the commercial and
       *  advertising-disclosure rules end up requiring. */
      type: "SPONSORED_SUPPLIER";
      label: string;
      supplier: FeedSupplier;
    });

export interface CommunityFeed {
  sections: FeedSection[];
}

/**
 * A rail with almost nothing in it looks worse than no rail at all --
 * the same "silence is the honest answer" rule the track record
 * follows. Applied in the app rather than trusted from the server, so
 * a thin section can never slip through from either side.
 */
export const MIN_ITEMS_PER_RAIL = 3;
