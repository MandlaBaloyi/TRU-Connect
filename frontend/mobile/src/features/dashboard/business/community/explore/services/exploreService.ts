import { Building2, Factory, Store, Truck, Warehouse } from "lucide-react-native";
import type { LucideIcon } from "lucide-react-native";

import { apiGet } from "@/services/api/apiClient";

import type { FeedSupplier } from "../../types";

/**
 * Browsing suppliers by what they ARE.
 *
 * NO MOCK SWITCH, matching feedDetailService's own reasoning: the
 * endpoint exists, and a fake list of wholesalers would mean designing
 * against a market nobody has. An empty real screen is truer to look at
 * than a full imaginary one.
 *
 * THE KINDS COME BACK WITH THE RESULTS, in one call, and that is
 * deliberate rather than lazy. The server builds the chip list from
 * kinds that actually HAVE somebody to show, so the two can never
 * disagree -- fetching them separately would open a window where the
 * app draws a chip whose result set is already empty, and an empty
 * result from a filter the app offered reads as broken.
 */

export interface ExplorePage {
  suppliers: FeedSupplier[];
  /** SupplierKind values that have at least one visible supplier with
   *  stock. Never contains UNSPECIFIED — "browse the ones who didn't
   *  say what they are" is not a thing anybody taps. */
  kinds: string[];
  total: number;
}

export async function getExplore(kind?: string): Promise<ExplorePage> {
  const query = kind ? `?kind=${encodeURIComponent(kind)}` : "";
  const data = await apiGet<ExplorePage>(`/community/explore${query}`);
  return {
    suppliers: data?.suppliers ?? [],
    kinds: data?.kinds ?? [],
    total: data?.total ?? 0,
  };
}

/** The app's words for the server's enum values.
 *
 *  PLURAL, because each one labels a group rather than a single
 *  supplier — "Wholesalers", not "Wholesaler". A chip names what you
 *  will get, not what each row is. */
export const SUPPLIER_KIND_LABELS: Record<string, string> = {
  WHOLESALER: "Wholesalers",
  DISTRIBUTOR: "Distributors",
  MANUFACTURER: "Manufacturers",
  RETAILER: "Retailers",
};

/** An unrecognised kind is TITLE-CASED rather than dropped. The server
 *  may add one before the app knows about it, and a chip labelled
 *  "Importers" is better than a gap in the row — same
 *  forward-compatibility rule the feed's section types already follow. */
/** One icon per supplier kind, beside the labels and for the same
 *  reason: the feed's doorway list and this screen's chip row must
 *  never disagree about what a wholesaler looks like.
 *
 *  ICONS, NOT PHOTOGRAPHS — the same argument CategoryIcon makes at
 *  length. lucide is already a dependency, a line drawing never
 *  competes with the supplier's own branding beside it, and four
 *  stock photos of warehouses would date badly and cost money.
 *
 *  THEY SAY WHAT THE BUSINESS DOES, NOT WHAT IT SELLS. A wholesaler
 *  holds stock (a warehouse), a distributor moves it (a truck), a
 *  manufacturer makes it (a factory), a retailer sells it over a
 *  counter (a shopfront). That is the actual distinction the kind
 *  encodes, so it is the one the glyphs should carry. */
export const SUPPLIER_KIND_ICONS: Record<string, LucideIcon> = {
  WHOLESALER: Warehouse,
  DISTRIBUTOR: Truck,
  MANUFACTURER: Factory,
  RETAILER: Store,
};

/** An unrecognised kind gets a neutral building rather than nothing.
 *  Same forward-compatibility rule labelForKind follows: the server may
 *  add a kind before the app knows about it, and a generic glyph is
 *  better than a hole where every other row has one. */
export function iconForKind(kind: string): LucideIcon {
  return SUPPLIER_KIND_ICONS[kind] ?? Building2;
}

export function labelForKind(kind: string): string {
  return (
    SUPPLIER_KIND_LABELS[kind] ??
    kind.charAt(0) + kind.slice(1).toLowerCase().replace(/_/g, " ")
  );
}
