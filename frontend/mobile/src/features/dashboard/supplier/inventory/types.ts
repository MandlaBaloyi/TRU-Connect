/**
 * Inventory answers one question: "how much of each product can I
 * currently sell?" -- distinct from Products' own "what do I sell?".
 * A genuinely separate Account tool (own tile, own routes), same
 * standing as Bulk Products, not a mode of the Products screen.
 *
 * NEVER DUPLICATES PRODUCT DATA -- no name/price/category/images live
 * here, only a reference (productId) plus quantity. The UI composes a
 * product + its inventory record together for display; the two stay
 * separate underlying resources, same reasoning as this whole app's
 * "every owned record gets one indexed reference column, not a join"
 * convention (see products/types.ts's own Product.supplierId doc
 * comment for the identical argument applied elsewhere).
 *
 * SCOPING DECISION, STATED EXPLICITLY: Products' own two-state
 * stockStatus (IN_STOCK/OUT_OF_STOCK, manually set on Add/Edit
 * Product) is NOT migrated to read from Inventory in this pass. The
 * design notes this was built against are clear that Products
 * "eventually" should just display whatever Inventory computes --
 * but that means removing/changing the stock control on
 * AddProductScreen, EditProductScreen, ProductCard, and BulkEditScreen,
 * all of which are already shipped and working. That's a real,
 * deliberate follow-up decision, not something to fold in silently
 * here. For now: Inventory computes its OWN three-state status
 * (IN_STOCK/LOW_STOCK/OUT_OF_STOCK) from quantity, shown only within
 * Inventory's own screens. Nothing about Products changes.
 *
 * quantityReserved EXISTS IN THE SCHEMA BUT IS ALWAYS 0 FOR NOW --
 * schema-ready for when Orders exists and can actually reserve stock
 * against a real order, same "add the field while cheap, wire the
 * behaviour later" pattern already used for Product.unitQuantity/
 * unitMeasure. No reservation LOGIC exists yet because there's nothing
 * to reserve against.
 *
 * Stock movement history (inventory_movements, an auditable log of
 * every adjustment) is explicitly NOT built yet either, per the
 * design notes' own "I wouldn't build this before your basic
 * Products -> Inventory -> Orders flow works" -- adjustStock still
 * takes a `reason`, so that history is cheap to add later without
 * changing this contract.
 */

import type { Product } from "../products/types";

/**
 * Three states, computed, never stored as a supplier's own choice --
 * the entire point of Inventory per the design notes: "don't make
 * suppliers manually manage status... TRU Connect calculates it."
 * Deliberately a DIFFERENT type from products/types.ts's own
 * StockStatus (two states, manually set) -- conflating the two would
 * imply they're interchangeable when they're answering different
 * questions until the scoping decision above gets revisited.
 */
export type InventoryStatus = "IN_STOCK" | "LOW_STOCK" | "OUT_OF_STOCK";

export interface InventoryItem {
  id: string;
  productId: string;
  supplierId: string;
  quantityOnHand: number;
  /** Always 0 today -- see this file's own header docstring. */
  quantityReserved: number;
  lowStockThreshold: number;
  createdAt: string;
  updatedAt: string;
}

/**
 * The UI's own composed view -- a product plus its inventory record
 * plus the two computed values (status, availableQuantity) so screens
 * never recompute them independently. NOT a persisted shape; assembled
 * at the API layer from two separate underlying resources.
 */
export interface InventoryListItem {
  product: Pick<
    Product,
    | "id"
    | "name"
    | "category"
    | "priceCents"
    | "compareAtPriceCents"
    | "sellingUnit"
    | "images"
    | "isArchived"
    | "productCode"
  >;
  inventory: InventoryItem;
  status: InventoryStatus;
  availableQuantity: number;
}

export type InventoryFilter = "ALL" | "IN_STOCK" | "LOW_STOCK" | "OUT_OF_STOCK";

export interface InventoryFilters {
  searchTerm?: string;
  filter?: InventoryFilter;
}

export interface InventorySummary {
  totalProducts: number;
  inStockCount: number;
  lowStockCount: number;
  outOfStockCount: number;
}

/**
 * "Suppliers don't think 'I currently have 47', they think 'I received
 * another 5 cases'" -- per the design notes' own reasoning for why
 * adjustment (a signed delta), not re-typing an absolute quantity, is
 * the primary interaction. quantityDelta is signed: positive receives
 * stock, negative removes it (sold outside TRU Connect, damaged,
 * etc.) -- both directions are the same operation, not two different
 * ones.
 */
export type StockAdjustmentReason = "STOCK_RECEIVED" | "STOCK_SOLD" | "DAMAGED" | "RETURNED" | "MANUAL_ADJUSTMENT";

export const STOCK_ADJUSTMENT_REASON_OPTIONS: { value: StockAdjustmentReason; label: string }[] = [
  { value: "STOCK_RECEIVED", label: "New stock received" },
  { value: "STOCK_SOLD", label: "Stock sold" },
  { value: "DAMAGED", label: "Damaged" },
  { value: "RETURNED", label: "Returned" },
  { value: "MANUAL_ADJUSTMENT", label: "Manual adjustment" },
];

export interface StockAdjustmentInput {
  productId: string;
  quantityDelta: number;
  reason: StockAdjustmentReason;
}

export interface SetLowStockThresholdInput {
  productId: string;
  lowStockThreshold: number;
}

export class InventoryError extends Error {
  code: string;

  constructor(message: string, code: string) {
    super(message);
    this.name = "InventoryError";
    this.code = code;
  }
}

/**
 * Inventory settings -- reached via the "⋮" menu, not per-product.
 * defaultLowStockThreshold seeds every NEW product's inventory record
 * (see api/mockInventoryApi.ts's own getOrCreateInventoryItem) --
 * changing it here doesn't retroactively change existing products'
 * own thresholds, which stay individually editable from each
 * product's own detail screen.
 *
 * lowStockAlertChannel is a real, saved PREFERENCE -- actually
 * sending an alert (push notification or email) needs backend
 * infrastructure that doesn't exist yet (no notification service, no
 * email sending tied to inventory). Saving the choice is honest and
 * useful now; delivering on it is a real, separate, backend-dependent
 * piece of work, not something to fake here.
 */
export type LowStockAlertChannel = "IN_APP" | "EMAIL";

export interface InventorySettings {
  defaultLowStockThreshold: number;
  lowStockAlertChannel: LowStockAlertChannel;
}
