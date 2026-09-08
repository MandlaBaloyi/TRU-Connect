/**
 * The SUPPLIER's own view of their storefront configuration -- which
 * of the six sections run, in what order, and which products are in
 * the two they choose themselves.
 *
 * DELIBERATELY A DIFFERENT SHAPE from what a BUSINESS receives
 * (business/find-supplier/storefront/types.ts). That one carries built
 * sections with full product objects, ready to render. This one
 * carries configuration: toggles, positions, and product IDs. A
 * supplier editing their shopfront and a business browsing it need
 * genuinely different things, and one shared type would end up being
 * neither.
 *
 * IT INCLUDES DISABLED SECTIONS, which the business-facing payload
 * never does. Without them there would be no way to switch one back
 * on.
 */

export type StorefrontSectionType =
  | "ON_SALE"
  | "BEST_SELLERS"
  | "NEW_ARRIVALS"
  | "BULK_VALUE"
  | "FEATURED_PRODUCT"
  | "CURATED";

export interface StorefrontConfigSection {
  /** Absent for a computed section the supplier has never configured
   *  -- it exists as a default rather than a row. Present once they
   *  save anything. */
  id?: string;
  type: StorefrontSectionType;
  isEnabled: boolean;
  position: number;
  /** True for the four the platform derives. A computed section has no
   *  editable title and no product list; the supplier only chooses
   *  whether it runs and where. */
  isComputed: boolean;
  /** CURATED only -- the supplier's own words for their own shelf. */
  title: string | null;
  /** CURATED only. An optional second line under the title. */
  subtitle?: string | null;
  /** FEATURED_PRODUCT and CURATED only. */
  productIds: string[];
}

export interface StorefrontConfig {
  sections: StorefrontConfigSection[];
}

/**
 * What each section is, in the supplier's own terms.
 *
 * WRITTEN FOR SOMEONE DECIDING WHETHER TO RUN IT, not describing the
 * query behind it. A supplier does not care that best sellers counts
 * units from CONFIRMED orders; they care that it only shows things
 * businesses have actually bought, and that it stays empty until some
 * have. Each line says what appears and what makes it appear, because
 * "why is my section not showing" is the question this screen has to
 * answer before it is asked.
 */
export const SECTION_COPY: Record<
  StorefrontSectionType,
  { title: string; description: string }
> = {
  ON_SALE: {
    title: "On sale now",
    description: "Products where you set a 'was' price higher than what you're charging now.",
  },
  BEST_SELLERS: {
    title: "What businesses buy most",
    description: "Your real order history. Stays empty until businesses have actually bought from you.",
  },
  NEW_ARRIVALS: {
    title: "Just added",
    description: "Anything you added in the last 45 days. Disappears when you haven't added recently.",
  },
  BULK_VALUE: {
    title: "Better per unit in bulk",
    description: "Products sold in packs, cheapest per item first. Needs a pack size on the product.",
  },
  FEATURED_PRODUCT: {
    title: "Your pick",
    description: "One product, shown large at the top of your profile. You choose it.",
  },
  CURATED: {
    title: "Your own shelf",
    description: "Products you choose, under a title you write — like 'Stock up for month-end'.",
  },
};

/** Matches the backend's own rules (supplier_storefront_service), so a
 *  supplier is stopped here rather than by a 422 after saving. */
export const MIN_CURATED_PRODUCTS = 3;
export const MAX_SECTION_PRODUCTS = 6;
export const MAX_CURATED_SECTIONS = 5;
export const MAX_SUBTITLE_LENGTH = 80;

/**
 * WHY "SHELF" AND NOT "COLLECTION". Collection is what e-commerce
 * normally calls this, and it is the word a supplier would recognise
 * fastest -- except that TruConnect already uses "collection" for
 * something else entirely: collect-versus-deliver, and the supplier's
 * own collection address. Two meanings for one word, on screens a
 * supplier moves between, is a support conversation waiting to happen.
 *
 * "Shelf" is concrete, needs no explaining to anyone who has stocked a
 * shop, and collides with nothing. It is copy, so it is cheap to
 * change -- but change it everywhere, including the backend's
 * validation messages.
 */
