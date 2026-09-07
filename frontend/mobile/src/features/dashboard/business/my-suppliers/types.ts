/**
 * Types specific to a business browsing a connected supplier's own
 * catalogue -- distinct from find-supplier/types.ts's own
 * SupplierProduct/SupplierProductDetail (the raw shapes the backend
 * sends), and from products/types.ts's own SortOption (the SUPPLIER's
 * own product-management sort, which includes a "Stock first" option
 * that only makes sense with a supplier's own inventory visibility --
 * not meaningful here, deliberately not reused as-is).
 */

export type CatalogSortOption =
  | "RECOMMENDED"
  | "BEST_SELLING"
  | "NEWEST"
  | "NAME_ASC"
  | "PRICE_ASC"
  | "PRICE_DESC";

/** RECOMMENDED is FIRST and is the default. It ranks in stock -> deepest
 *  discount -> newest (the same rule the brand-profile showcase uses,
 *  applied in SQL so it survives pagination). NEWEST used to be the
 *  default, which meant whatever a supplier uploaded last led their
 *  shop regardless of whether it was even orderable. */
export const CATALOG_SORT_OPTIONS: { value: CatalogSortOption; label: string }[] = [
  { value: "RECOMMENDED", label: "Recommended" },
  { value: "BEST_SELLING", label: "Best selling" },
  { value: "NEWEST", label: "Newest" },
  { value: "NAME_ASC", label: "Name (A-Z)" },
  { value: "PRICE_ASC", label: "Price (low to high)" },
  { value: "PRICE_DESC", label: "Price (high to low)" },
];

/** null means "every category" -- deliberately not its own
 *  {value:"ALL"} entry in the options list; CatalogCategoryFilterSheet
 *  renders "All categories" as a real row that sets the selection back
 *  to null, rather than treating "all" as a category value that would
 *  need to be excluded from the real category list everywhere else. */
export type CatalogCategoryFilter = string | null;

// DisconnectReason/ReportReason live in find-supplier/types.ts, not
// here -- that's where endConnection/reportSupplier themselves live
// (find-supplier/services/), and my-suppliers already imports several
// other types from there (SupplierProduct, SupplierProductDetail).
// Defining them here instead would create a backward dependency
// (find-supplier importing FROM my-suppliers) against that same
// established direction.
export type { DisconnectReason, ReportReason } from "../find-supplier/types";
export { DISCONNECT_REASONS, REPORT_REASONS } from "../find-supplier/types";
