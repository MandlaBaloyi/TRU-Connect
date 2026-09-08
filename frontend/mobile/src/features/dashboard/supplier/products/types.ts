/**
 * Products — a supplier's own catalogue of what they sell. This is the
 * LOCKED real contract, not a shape invented for a mock and rewritten
 * later -- the mock in api/mockProductsApi.ts and the (not-yet-wired)
 * real backend in api/httpProductsApi.ts both conform to exactly this
 * shape.
 *
 * v2 of this file (post first-round review): controlled category
 * taxonomy expanded from 6 to 16 values, units expanded from 3 to 12,
 * images went from a single field to an ordered array, archiving added
 * as its own lifecycle concern distinct from stock status. See each
 * section below for the specific reasoning kept with the thing it
 * explains, not centralised here.
 *
 * Money: integer cents, never a float -- same convention as Loan Book/
 * Order Book (see order-book/types.ts's own Cents type). Kept as this
 * feature's own local alias rather than a cross-feature import, same
 * reasoning as every other per-feature type in this app.
 */

/** Integer cents. Never a float, never a formatted string. */
export type Cents = number;

/**
 * Two states only for MVP, not three -- "low stock" without any real
 * quantity tracking behind it would just be a third manual toggle with
 * no data to justify it. Add LOW_STOCK later as a pure enum extension
 * once Inventory (quantity tracking) is real; nothing here needs to
 * change shape to support that.
 *
 * ARCHIVING IS DELIBERATELY NOT A THIRD VALUE HERE -- see Product's own
 * `isArchived` field below. Stock status answers "can this be ordered
 * right now"; archived answers "is this still part of the catalogue at
 * all". A product can be OUT_OF_STOCK and still fully active (about to
 * be restocked), or archived while its last known stock status was
 * IN_STOCK -- the two are genuinely orthogonal, not one three-state
 * enum wearing two hats.
 */
export type StockStatus = "IN_STOCK" | "OUT_OF_STOCK";

/**
 * TRU-CONNECT-CONTROLLED taxonomy, not free text and not
 * supplier-created -- free text fragments badly across suppliers
 * ("Drinks" vs "drinks" vs "Beverages"), which breaks filtering and
 * search the moment more than one supplier is on the platform. Flat
 * list (not nested) matching exactly what was reviewed and approved --
 * "Food & Grocery" is its own catch-all value alongside the more
 * specific food categories, not a parent/section header, since that's
 * how it was shown in the approved Select Category example (no
 * indentation, no grouping).
 *
 * Picked via a searchable picker (components/CategoryPickerModal.tsx),
 * never rendered as 16 buttons on the Add Product form -- that's
 * exactly the "ugly at scale" problem flagged in review, same
 * reasoning that already applied to keeping stock_status to two states.
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
  | "BABY_FAMILY"
  | "STATIONERY_SCHOOL"
  | "HARDWARE_GENERAL"
  | "ELECTRONICS_ACCESSORIES"
  | "PACKAGING_DISPOSABLE"
  | "CLOTHING_APPAREL"
  | "OTHER";

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
  { value: "BABY_FAMILY", label: "Baby & Family" },
  { value: "STATIONERY_SCHOOL", label: "Stationery & School" },
  { value: "HARDWARE_GENERAL", label: "Hardware & General" },
  { value: "ELECTRONICS_ACCESSORIES", label: "Electronics & Accessories" },
  { value: "PACKAGING_DISPOSABLE", label: "Packaging & Disposable" },
  { value: "CLOTHING_APPAREL", label: "Clothing & Apparel" },
  { value: "OTHER", label: "Other" },
];

/**
 * Expanded from 3 to 12 per review -- "allow the backend to add more
 * units later without changing the product architecture" is honoured
 * by keeping this a plain string-backed union (cheap to extend) rather
 * than, say, a hardcoded numeric enum. Picked via the same
 * SelectFieldModal pattern as category (components/UnitPickerModal.tsx)
 * rather than 12 inline chips -- same "ugly at scale" reasoning.
 */
export type ProductUnit =
  | "EACH"
  | "PACK"
  | "BOX"
  | "CASE"
  | "BAG"
  | "BOTTLE"
  | "CAN"
  | "DOZEN"
  | "KG"
  | "G"
  | "L"
  | "ML";

export const UNIT_OPTIONS: { value: ProductUnit; label: string }[] = [
  { value: "EACH", label: "Each" },
  { value: "PACK", label: "Pack" },
  { value: "BOX", label: "Box" },
  { value: "CASE", label: "Case" },
  { value: "BAG", label: "Bag" },
  { value: "BOTTLE", label: "Bottle" },
  { value: "CAN", label: "Can" },
  { value: "DOZEN", label: "Dozen" },
  { value: "KG", label: "kg" },
  { value: "G", label: "g" },
  { value: "L", label: "L" },
  { value: "ML", label: "ml" },
];

export interface Product {
  id: string;
  /** supplier_profile_id, denormalized on every row -- same reasoning
   *  as every other owned-record shape in this app (Order Book's own
   *  Order.businessId doc comment has the full argument): every
   *  authorization/scoping check needs one indexed column, not a join. */
  supplierId: string;
  name: string;
  category: ProductCategory;
  priceCents: Cents;
  /** What the price is FOR -- e.g. "Case" for a case-priced product.
   *  Renamed conceptually to "Sold as" in the UI (matches the approved
   *  Add Product mockup) but kept as `sellingUnit` here since it's the
   *  unit the PRICE applies to, which matters once unitQuantity below
   *  is real and there's a second, different unit in play. */
  sellingUnit: ProductUnit;
  /**
   * How many `unitMeasure` are contained in one `sellingUnit` -- e.g.
   * a "Case" of Coca-Cola 500ml containing 24 bottles: sellingUnit =
   * CASE, unitQuantity = 24, unitMeasure = BOTTLE. SCHEMA-READY, NOT
   * YET SURFACED IN THE UI -- deliberately deferred per review ("don't
   * let those fields destroy the first experience"/"eventually"
   * framing): Add Product only asks for `sellingUnit` right now.
   * Both fields are optional/nullable so a plain "sold each" product
   * (sellingUnit = EACH) never needs them populated at all. When the UI
   * for this lands, businesses ordering stock can specify "2 Cases"
   * instead of "48 bottles" -- see algorithms/unitPricing.ts for the
   * price-per-base-unit math this unlocks.
   */
  unitQuantity: number | null;
  unitMeasure: ProductUnit | null;
  /**
   * LEGACY, NO LONGER MANUALLY SET -- Inventory (a separate feature)
   * now owns real stock status, computed from actual quantity
   * (IN_STOCK/LOW_STOCK/OUT_OF_STOCK -- three states, not two).
   * Products' own screens (ProductCard, ProductDetailScreen) no
   * longer read this field; they fetch inventory-derived status
   * instead (see ProductsScreen.tsx and ProductDetailScreen.tsx's own
   * docstrings for exactly how). Kept on the type rather than removed
   * outright to avoid a wider breaking change in this pass -- Bulk
   * Edit's own "Update Stock" action was retired specifically because
   * it wrote to this now-unread field (see bulk-products/screens/
   * BulkEditScreen.tsx's own docstring).
   */
  stockStatus: StockStatus;
  /**
   * ORDERED array, first element is ALWAYS the primary/cover image --
   * no separate `isPrimary` flag on each entry. Per review: "the
   * supplier doesn't have to understand what a primary image is, TRU
   * Connect just handles it" -- order IS the mechanism, not a field a
   * UI has to explain. Empty array (not null) when nothing's been
   * uploaded yet, so every consumer can just check `.length` /
   * `images[0]` without a null check first.
   */
  images: string[];
  /**
   * The supplier's own tracking label -- Stock Keeping Unit. Optional
   * to type; left blank, the backend auto-fills a stable one
   * (SKU-0001, SKU-0002...) so every product still has something to
   * group sales/profit/order-count by. UNIQUE PER SUPPLIER, not
   * platform-wide -- matches how SKUs actually work in the real world.
   * Editable, unlike productCode below.
   */
  sku: string;
  /**
   * The short, human-readable stand-in for this product's own internal
   * id -- shown to both the supplier and any business ordering from
   * them, in place of a UUID nobody could read aloud. ALWAYS
   * server-generated, NEVER editable, anywhere -- this field is
   * deliberately absent from CreateProductInput/UpdateProductInput
   * below; there is nothing for a supplier to type, ever.
   */
  productCode: string;
  /** Plain text -- ingredients, case size ("3 loaves per case"),
   *  anything a supplier wants a business to see before ordering.
   *  Optional, null when never set. */
  description: string | null;
  /** The "was RX" comparison price for a sale/promotion -- null when
   *  not running one. Always strictly HIGHER than priceCents when set
   *  (enforced server-side); the UI shows it crossed out next to the
   *  real price, never the other way round. */
  compareAtPriceCents: Cents | null;
  /** Products aren't deleted, ever -- see this field's own reasoning
   *  at CreateProductInput and the Archive flow in ProductDetailScreen.
   *  Historical orders must keep referencing a real product row. */
  isArchived: boolean;
  /** Whether this product is "featured" on the supplier's business
   *  profile (SupplierPinnedProduct, max 6). Toggled from the ⋮ menu on
   *  each product card. The backend's list endpoint sends the real
   *  value; single-product / bulk responses default it false, so treat
   *  the list as the source of truth. */
  isPinned: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateProductInput {
  name: string;
  category: ProductCategory;
  priceCents: Cents;
  sellingUnit: ProductUnit;
  /** WHAT IS INSIDE the unit -- "Case" + 6 + "Bottle" reads as "Case
   *  of 6 bottles". Both optional and only meaningful together; a
   *  product genuinely sold as Each has neither.
   *
   *  Both columns have existed on the backend Product model from the
   *  beginning and no input type ever carried them, so nothing could
   *  set them -- which left the per-unit price, the pack label and the
   *  storefront's better-per-unit section all reading a field that was
   *  always null. */
  unitQuantity?: number;
  unitMeasure?: ProductUnit;
  /** LOCAL, unuploaded file URIs from the on-device picker
   *  (components/ProductPhotosField.tsx) -- never Cloudinary URLs at
   *  this stage. ORDERED; first = cover image, matching Product.images'
   *  own convention exactly, so nothing needs to change shape once
   *  Cloudinary (sub-goal 3) starts actually uploading these. */
  localImageUris: string[];
  /** Optional -- left blank/undefined, the backend auto-generates one.
   *  productCode is deliberately absent here: never typed, always
   *  server-generated. See Product.sku's own docstring. */
  sku?: string;
  description?: string;
  compareAtPriceCents?: Cents;
}

/**
 * Edit Product's own input -- same fields as CreateProductInput plus
 * the id being updated, `images` renamed back from `localImageUris`
 * since an edit's image array is a MIX of already-hosted URLs (kept
 * from before) and freshly-picked local URIs (added during this edit),
 * not purely local like a brand-new product's. The mock treats both
 * identically today (see ProductPhotosField's own docstring -- it only
 * ever hands back an ordered string[], regardless of origin); the real
 * implementation will need to diff this array against the product's
 * previous one to know which entries are new uploads.
 */
export interface UpdateProductInput {
  id: string;
  name: string;
  category: ProductCategory;
  priceCents: Cents;
  sellingUnit: ProductUnit;
  /** WHAT IS INSIDE the unit -- "Case" + 6 + "Bottle" reads as "Case
   *  of 6 bottles". Both optional and only meaningful together; a
   *  product genuinely sold as Each has neither.
   *
   *  Both columns have existed on the backend Product model from the
   *  beginning and no input type ever carried them, so nothing could
   *  set them -- which left the per-unit price, the pack label and the
   *  storefront's better-per-unit section all reading a field that was
   *  always null. */
  unitQuantity?: number;
  unitMeasure?: ProductUnit;
  images: string[];
  /** undefined means "leave the existing SKU alone" -- matches the
   *  backend's own update_product semantics exactly (see
   *  product_service.py's own docstring). Never re-generates a new
   *  one on the supplier's behalf; only creating a product does that.
   *  Still never productCode -- same reasoning as CreateProductInput. */
  sku?: string;
  description?: string;
  compareAtPriceCents?: Cents;
}

/**
 * The list screen's own filter dimension -- deliberately NOT the same
 * type as StockStatus. "Archived" is a lifecycle filter, not a stock
 * state (see StockStatus's own docstring) -- keeping it a separate
 * union means the persisted stock_status enum on Product never has to
 * grow a value that doesn't actually describe stock.
 */
export type ProductListFilter = "ALL" | "IN_STOCK" | "OUT_OF_STOCK" | "ARCHIVED";

export interface ProductFilters {
  searchTerm?: string;
  listFilter?: ProductListFilter;
}

/**
 * List-screen sort options -- client-side only, applied on top of
 * whatever the current filter/search already narrowed down to.
 * NEWEST matches the API's own default ordering (mock and http both
 * already return newest-first), so selecting it is a no-op sort, not
 * a special case the sort function needs to handle differently.
 */
export type SortOption = "NEWEST" | "NAME_ASC" | "PRICE_ASC" | "PRICE_DESC" | "STOCK_FIRST";

export const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: "NEWEST", label: "Newest first" },
  { value: "NAME_ASC", label: "Name (A-Z)" },
  { value: "PRICE_ASC", label: "Price (low to high)" },
  { value: "PRICE_DESC", label: "Price (high to low)" },
  { value: "STOCK_FIRST", label: "In stock first" },
];

export class ProductsError extends Error {
  code: string;
  fieldErrors: Record<string, string>;

  constructor(message: string, code: string, fieldErrors: Record<string, string> = {}) {
    super(message);
    this.name = "ProductsError";
    this.code = code;
    this.fieldErrors = fieldErrors;
  }
}
