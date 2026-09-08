import type { SupplierProduct } from "../types";

/**
 * A supplier's storefront: the merchandised sections above their
 * category strips.
 *
 * WHY SECTIONS AND NOT ONE LONG LIST. The profile already shows every
 * product grouped by category, each strip drawn identically -- which
 * is a catalogue, not a shopfront. Nothing on it can say "this is on
 * sale", "this is what everyone buys", or "this is the one to look at
 * first". A real listing earns attention by presenting DIFFERENT
 * products DIFFERENTLY, and that difference is the point of this file.
 *
 * EACH TYPE GETS ITS OWN CARD, deliberately -- not one card with a
 * badge swapped in:
 *
 *   FEATURED_PRODUCT -- full width, the only product on the screen
 *                       that gets its own block. One per profile.
 *   ON_SALE          -- a corner ribbon and the old price struck
 *                       through. Urgency, and the saving is the
 *                       headline rather than the name.
 *   BEST_SELLERS     -- a rank numeral. "Everyone buys this" is a
 *                       different claim from "this is cheap", and a
 *                       ranked list says it in a way a badge cannot.
 *   NEW_ARRIVALS     -- a "NEW" flag and nothing else competing with
 *                       it. Answers "what has changed since I last
 *                       ordered", which is the question a repeat buyer
 *                       actually arrives with.
 *   CURATED          -- the supplier's own themed strip, titled by
 *                       them. The only section whose meaning the
 *                       platform does not decide.
 *   BULK_VALUE       -- leads with the PER-UNIT price. This is the one
 *                       that has nothing to do with consumer apps and
 *                       everything to do with wholesale: a pack of 6
 *                       and a pack of 24 at the same price are
 *                       completely different offers, and an informal
 *                       buyer comparing suppliers is really comparing
 *                       per-item cost (see components/products/
 *                       unitEconomics.ts).
 *
 * SERVER-DRIVEN, SAME AS THE COMMUNITY FEED. The supplier's own
 * merchandising -- which section runs, in what order -- is a decision
 * that has to be changeable without an app release, and an unknown
 * type renders nothing rather than crashing an older build.
 *
 * THE CATEGORY STRIPS ARE NOT IN HERE. SupplierShowcase already draws
 * those and draws them well; these sections sit above it. Folding both
 * into one contract is a later step, only worth doing once these have
 * been reviewed on a real screen.
 */

interface SectionBase {
  id: string;
}

export type StorefrontSection =
  | (SectionBase & { type: "FEATURED_PRODUCT"; label: string; product: SupplierProduct })
  | (SectionBase & {
      type: "ON_SALE";
      title: string;
      subtitle?: string | null;
      products: SupplierProduct[];
    })
  | (SectionBase & {
      type: "BEST_SELLERS";
      title: string;
      subtitle?: string | null;
      products: SupplierProduct[];
    })
  | (SectionBase & {
      type: "BULK_VALUE";
      title: string;
      subtitle?: string | null;
      products: SupplierProduct[];
    })
  | (SectionBase & {
      type: "NEW_ARRIVALS";
      title: string;
      subtitle?: string | null;
      products: SupplierProduct[];
    })
  | (SectionBase & {
      /** A strip the SUPPLIER titles themselves -- "Stock up for
       *  month-end", "Braai weekend", "Back to school". The section
       *  types above each encode a rule the platform can compute; this
       *  one encodes a judgement only the person selling knows how to
       *  make, and month-end in particular is the single biggest
       *  rhythm in South African informal retail.
       *
       *  It is also the section a wholesaler will ask for first, which
       *  is the second reason it exists now: a partner wanting their
       *  own range promoted needs somewhere to put it that is not a
       *  code change. */
      type: "CURATED";
      title: string;
      subtitle?: string | null;
      products: SupplierProduct[];
    });

export interface SupplierStorefront {
  sections: StorefrontSection[];
}

/** Same rule as the Community feed: a strip with almost nothing in it
 *  reads as a broken shelf rather than a short one. */
export const MIN_ITEMS_PER_STOREFRONT_SECTION = 3;
