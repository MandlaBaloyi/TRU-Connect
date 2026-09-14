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

export interface BrowseResult {
  products: BrowseProduct[];
  hasMore: boolean;
}
