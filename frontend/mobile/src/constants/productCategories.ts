/**
 * The product category taxonomy — the ONE definition.
 *
 * TRU-CONNECT-CONTROLLED, not free text and not supplier-created. Free
 * text fragments badly across suppliers ("Drinks" vs "drinks" vs
 * "Beverages"), which breaks filtering and search the moment more than
 * one supplier is on the platform. Flat list (not nested) matching what
 * was reviewed and approved — "Food & Grocery" is its own catch-all
 * value alongside the more specific food categories, not a parent or
 * section header, since that is how it was shown in the approved Select
 * Category example (no indentation, no grouping).
 *
 * Picked via a searchable picker (CategoryPickerModal), never rendered
 * as seventeen buttons on the Add Product form — the "ugly at scale"
 * problem flagged in review, the same reasoning that keeps stock_status
 * to two states.
 *
 * WHY IT LIVES IN constants/ RATHER THAN THE SUPPLIER FEATURE FOLDER.
 * It used to live in features/dashboard/supplier/products/types.ts, and
 * three BUSINESS screens imported it from there through
 * "../../../supplier/products/types" — business code reaching into a
 * supplier feature for a shared vocabulary. The taxonomy belongs to
 * neither role: a supplier files a product under it and a business
 * filters by it. That old path still re-exports these names so nothing
 * broke in the move.
 *
 * KEEP IN STEP WITH THE BACKEND. This mirrors
 * backend/src/domains/catalogue/products/models/taxonomy.py, which is
 * authoritative — the column is a native Postgres enum, so a value
 * here that does not exist there fails at write time, not compile
 * time. BEAUTY_HAIR was added there on 2026-09-13 and the app went a
 * day without it; that gap is exactly what this note is for.
 */

export type ProductCategory =
  | "FOOD_GROCERY"
  | "BEVERAGES"
  | "SNACKS_CONFECTIONERY"
  | "BAKERY"
  | "DAIRY_CHILLED"
  | "FRESH_PRODUCE"
  | "MEAT_FROZEN"
  | "HOUSEHOLD_CLEANING"
  | "PERSONAL_CARE"
  | "BEAUTY_HAIR"
  | "BABY_FAMILY"
  | "STATIONERY_SCHOOL"
  | "HARDWARE_GENERAL"
  | "ELECTRONICS_ACCESSORIES"
  | "PACKAGING_DISPOSABLE"
  | "CLOTHING_APPAREL"
  | "OTHER";

/**
 * Canonical order. Several screens order their own filters against this
 * rather than against whatever order the server happened to return, so
 * reordering this list reorders them too.
 *
 * BEAUTY_HAIR SITS NEXT TO PERSONAL_CARE, not at the end where a new
 * value would naturally land. They are adjacent in a shopper's head and
 * the split between them is the whole reason it exists: Personal Care
 * is soap and toothpaste, Beauty & Hair is wigs, relaxers, cosmetics
 * and nails — a different supplier on a different rhythm.
 */
export const CATEGORY_OPTIONS: { value: ProductCategory; label: string }[] = [
  { value: "FOOD_GROCERY", label: "Food & Grocery" },
  { value: "BEVERAGES", label: "Beverages" },
  { value: "SNACKS_CONFECTIONERY", label: "Snacks & Confectionery" },
  { value: "BAKERY", label: "Bakery" },
  { value: "DAIRY_CHILLED", label: "Dairy & Chilled" },
  { value: "FRESH_PRODUCE", label: "Fresh Produce" },
  { value: "MEAT_FROZEN", label: "Meat & Frozen" },
  { value: "HOUSEHOLD_CLEANING", label: "Household & Cleaning" },
  { value: "PERSONAL_CARE", label: "Personal Care" },
  { value: "BEAUTY_HAIR", label: "Beauty & Hair" },
  { value: "BABY_FAMILY", label: "Baby & Family" },
  { value: "STATIONERY_SCHOOL", label: "Stationery & School" },
  { value: "HARDWARE_GENERAL", label: "Hardware & General" },
  { value: "ELECTRONICS_ACCESSORIES", label: "Electronics & Accessories" },
  { value: "PACKAGING_DISPOSABLE", label: "Packaging & Disposable" },
  { value: "CLOTHING_APPAREL", label: "Clothing & Apparel" },
  { value: "OTHER", label: "Other" },
];

/**
 * FALLS BACK TO THE RAW VALUE, never to "Unknown". If the backend adds
 * a category before the app ships, a business should see
 * "BEAUTY_HAIR" — ugly, readable, obviously a gap — rather than a
 * confident "Other" that hides it. Three screens each wrote this line
 * themselves before it lived here.
 */
export function categoryLabel(value: ProductCategory | string): string {
  return CATEGORY_OPTIONS.find((option) => option.value === value)?.label ?? String(value);
}
