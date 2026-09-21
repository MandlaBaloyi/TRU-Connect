/**
 * Browsing stock across every supplier.
 *
 * A DIFFERENT SHAPE FROM find-supplier's, on purpose. That one finds
 * SHOPS and its cards describe a supplier; this finds STOCK, and every
 * card has to name whose it is because a browse mixes suppliers where a
 * shopfront never does.
 */

export interface BrowseProduct {
  id: string;
  supplierId: string;
  supplierName: string;
  name: string;
  category: string | null;
  imageUrl: string | null;
  priceCents: number;
  /** Struck-through original — null when not discounted. */
  compareAtPriceCents: number | null;
  /** The CHEAPEST offer of this product across every supplier who has
   *  it. Equal to priceCents when the shown offer is the cheapest,
   *  which is the common case — the card only says "from" when
   *  somebody else is cheaper, so the word always means something. */
  fromPriceCents: number;
  inStock: boolean;
  /** HOW MANY OTHER SUPPLIERS carry this same product — the resolved
   *  catalogue made visible, and the one thing on this screen a
   *  competitor without one cannot draw.
   *
   *  Zero until matching links offers together, which is the honest
   *  state today: the card simply does not mention alternatives. */
  alternativeCount: number;
  /** How many DISTINCT businesses have bought this. null when nobody
   *  has — never 0. Counts BUSINESSES, not units, so one wholesale
   *  buyer cannot manufacture a bestseller by ordering forty cases. */
  /** Same field the feed sends, so one rule renders both. */
  supplierVerificationStatus: string | null;
  buyerCount: number | null;
  /** The sentence, built server-side so this screen and the Community
   *  feed cannot word it differently. */
  buyerLabel: string | null;
}

/** One option in the filter row, with how many PRODUCTS it opens onto.
 *  The count is a promise: tap a chip saying 12 and twelve cards
 *  arrive. Shared by supplier kinds and supplier names, because they
 *  are the same control asking a different question. */
export interface BrowseFacet {
  id: string;
  name: string;
  count: number;
}

/** How the list is ordered. Matches the server's SORTS exactly; an
 *  unknown value falls back to name rather than erroring, so a stale
 *  app cannot break a browse. */
export type BrowseSort = "name" | "price_asc" | "price_desc";

export interface BrowseFilters {
  search?: string;
  /** WHAT SORT of business is selling it — wholesaler, distributor,
   *  manufacturer, retailer. Replaced brand chips: a category has
   *  dozens of brands and four kinds, and search answers "Huletts"
   *  better than any finite row of chips could. */
  kind?: string | null;
  /** One supplier, of whoever is already in scope. Narrows "my
   *  suppliers" rather than replacing it. */
  supplier?: string | null;
  /** Only suppliers this shop is connected to. A FILTER, not a
   *  permission: browsing is open at the platform level, and this is
   *  the shop asking for less rather than being shown less. */
  mineOnly?: boolean;
  sort?: BrowseSort;
}

export interface BrowseResult {
  products: BrowseProduct[];
  hasMore: boolean;
  /** OFFERS, NOT CARDS, and the header must say so. Grouping happens
   *  after the query, so a true card count would mean grouping the
   *  whole catalogue. Present only on the first page of a filter —
   *  every scroll after it re-uses what the header already has. */
  total?: number;
  kinds?: BrowseFacet[];
  /** WHO IS SELLING IT. Becomes the useful axis once a shop narrows to
   *  its own suppliers: "which of my four has this" decides whether an
   *  order is one delivery or three. */
  suppliers?: BrowseFacet[];
}
