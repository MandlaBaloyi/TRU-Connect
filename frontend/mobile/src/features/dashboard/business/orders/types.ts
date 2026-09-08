/**
 * business/orders -- the cart and checkout feature, communicating
 * with domains/network/orders on the backend (the "orders" blueprint,
 * /api/v1/checkout/... routes). Named "orders" on both sides
 * deliberately, matching the backend's own naming.
 */

export interface CartItem {
  productId: string;
  productName: string;
  images: string[];
  quantity: number;
  priceCentsAtAddTime: number;
  lineTotalCents: number;
  /** True when the product this item refers to has since been
   *  archived or deleted by the supplier. Still shown (a business
   *  should see what they added), never silently hidden -- checkout
   *  itself is where this genuinely blocks submission, not here. */
  isStale: boolean;
}

export interface Cart {
  id: string;
  supplierProfileId: string;
  supplierName: string;
  /** The supplier's public brand image, for the cart's own social top
   *  bar (avatar + name). Same ungated asset the catalogue and brand
   *  profile use; null when they haven't uploaded one. */
  supplierBusinessImageUrl: string | null;
  /** The supplier's own stated terms, carried on the cart so checkout
   *  can honour them without a second request. checkout_service
   *  enforces both for real; these let the UI be honest BEFORE the
   *  business fills in a whole form. */
  /** TRI-STATE — null means unstated; only an explicit false blocks
   *  a DELIVER order. */
  supplierOffersDelivery: boolean | null;
  /** null means no minimum — never 0. */
  supplierMinimumOrderCents: number | null;
  /** Where to collect. Null when the supplier hasn't set one. */
  supplierCollectionAddress: CartCollectionAddress | null;
  status: string;
  totalCents: number;
  itemCount: number;
  items: CartItem[];
}

/** Mirrors cart_service._collection_address_dict exactly. */
export interface CartCollectionAddress {
  building: string | null;
  street: string | null;
  suburb: string | null;
  city: string | null;
  province: string | null;
  postalCode: string | null;
  latitude: number | null;
  longitude: number | null;
}

// PaymentMethod is DEFINED ONCE, in dashboard/shared/payment. It used
// to be declared here AND in the other role's types.ts, identically --
// which is exactly how the backend ended up with a DIRECT value that
// three of five places had never heard of. Re-exported rather than
// moved so every existing import path keeps working.
import type { PaymentMethod } from "@/features/dashboard/shared/payment/paymentMethods";
export type { PaymentMethod };
export type DeliveryType = "DELIVER" | "COLLECT";

/**
 * The real status model, matching the backend's own StockOrderStatus
 * exactly. PENDING_SUPPLIER_APPROVAL is where DIRECT orders land --
 * money that moves outside TruConnect is not verified in real time, so
 * the order genuinely isn't settled yet and the supplier's own
 * accept/decline is a real decision. CONFIRMED is where a real PAYFAST
 * payment lands immediately (no supplier approval needed at all), and
 * where a pending order moves once a supplier approves it -- not
 * reachable yet, the approve action itself is real, separate,
 * supplier-side work. DECLINED is a supplier rejecting the order --
 * also not reachable yet, same reasoning.
 */
export type StockOrderStatus =
  | "CART"
  | "AWAITING_PAYMENT"
  | "PENDING_SUPPLIER_APPROVAL"
  | "CONFIRMED"
  | "DECLINED"
  | "CANCELLED";

const STATUS_LABELS: Record<StockOrderStatus, string> = {
  CART: "In cart",
  AWAITING_PAYMENT: "Awaiting payment",
  PENDING_SUPPLIER_APPROVAL: "Pending supplier approval",
  CONFIRMED: "Confirmed",
  DECLINED: "Declined",
  CANCELLED: "Cancelled",
};

/** The one place status display text is decided -- every screen
 *  showing an order's own status calls this, rather than each screen
 *  inventing its own label and risking drift between them. */
export function getStatusLabel(status: string): string {
  return STATUS_LABELS[status as StockOrderStatus] ?? status;
}

export interface SubmitCheckoutRequest {
  paymentMethod: PaymentMethod;
  deliveryType: DeliveryType;
  deliveryAddressText?: string | null;
  /** All optional -- COLLECT never sends any of these (the backend
   *  ignores them for COLLECT regardless), and an old client that
   *  predates the map picker can still submit with only
   *  deliveryAddressText, same as before. */
  deliveryBuilding?: string | null;
  deliveryStreet?: string | null;
  deliverySuburb?: string | null;
  deliveryCity?: string | null;
  deliveryProvince?: string | null;
  deliveryPostalCode?: string | null;
  deliveryLatitude?: number | null;
  deliveryLongitude?: number | null;
}

export interface CheckoutResult {
  id: string;
  /** The real, human-facing reference (TRU-XXXX-XXXXXX) -- what's
   *  actually shown to a person, everywhere. `id` still exists
   *  alongside it, but purely as an internal detail used to fetch
   *  this exact order's own full detail later, never rendered on
   *  screen. */
  orderReference: string;
  status: string;
  totalCents: number;
  instructions: string | null;
  redirectUrl: string | null;
}

export interface OrderHistoryEntry {
  id: string;
  orderReference: string;
  status: string;
  totalCents: number;
  itemCount: number;
  paymentMethod: PaymentMethod | null;
  deliveryType: DeliveryType | null;
  submittedAt: string | null;
}

export interface OrderDetailItem {
  productId: string;
  productName: string;
  images: string[];
  quantity: number;
  priceCentsAtAddTime: number;
  lineTotalCents: number;
}

export type DeclineReason = "out_of_stock" | "cannot_fulfil_delivery_area" | "pricing_error" | "suspected_fraud" | "no_response" | "other";

/** Mirrors supplier/stock-orders/types.ts's own DECLINE_REASON_LABELS
 *  intentionally, not imported from it -- these are two genuinely
 *  separate features (a supplier deciding to decline vs. a business
 *  reading why), and a tiny static lookup table is cheap enough to
 *  duplicate rather than reach across a domain boundary for. */
export const DECLINE_REASON_LABELS: Record<DeclineReason, string> = {
  out_of_stock: "Out of stock",
  cannot_fulfil_delivery_area: "Can't fulfil this delivery area",
  pricing_error: "Pricing error",
  suspected_fraud: "Suspected fraud",
  no_response: "No response in time",
  other: "Other reason",
};

/** The real, enforced subset a BUSINESS can choose from when
 *  cancelling their own still-PENDING order -- matches the backend's
 *  own BUSINESS_CANCEL_REASONS in cancellation_service.py exactly.
 *  Supplier-side reasons (out_of_stock etc.) live in
 *  supplier/stock-orders/types.ts's own CancelReason -- genuinely
 *  different vocabulary for a genuinely different actor, not the
 *  same list reused. */
export type CancelReason = "changed_mind" | "found_alternative" | "ordered_by_mistake" | "other";

export const CANCEL_REASON_LABELS: Record<CancelReason, string> = {
  changed_mind: "Changed my mind",
  found_alternative: "Found it elsewhere",
  ordered_by_mistake: "Ordered by mistake",
  other: "Other reason",
};

/** For DISPLAYING a cancel reason regardless of which side set it --
 *  a business's own Order Details view might show an order THEY
 *  cancelled (CANCEL_REASON_LABELS above covers that) or one the
 *  SUPPLIER cancelled after confirming (their own reason vocabulary:
 *  out_of_stock etc.) -- this superset covers both so the label
 *  lookup never comes back empty regardless of who acted. */
export const ANY_CANCEL_REASON_LABELS: Record<string, string> = {
  ...CANCEL_REASON_LABELS,
  out_of_stock: "Out of stock",
  cannot_fulfil_delivery_area: "Can't fulfil this delivery area",
  pricing_error: "Pricing error",
};

export interface OrderDetail {
  id: string;
  orderReference: string;
  status: string;
  totalCents: number;
  paymentMethod: PaymentMethod | null;
  deliveryType: DeliveryType | null;
  deliveryAddressText: string | null;
  submittedAt: string | null;
  /** Null while still PENDING_SUPPLIER_APPROVAL -- when the supplier
   *  actually approved or declined. */
  decidedAt: string | null;
  /** Snapshotted at the real moment of submission -- what was true
   *  about this business then, not a live value that could have
   *  silently changed since. See the backend's own StockOrder model
   *  comment for the full reasoning. */
  buyerName: string | null;
  buyerPhone: string | null;
  buyerEmail: string | null;
  buyerBusinessName: string | null;
  /** Only meaningful when status is "DECLINED" -- null otherwise. */
  declineReason: DeclineReason | null;
  declineDetails: string | null;
  /** Only meaningful when status is "CANCELLED". */
  cancelledBy: "business" | "supplier" | null;
  cancelReason: CancelReason | "out_of_stock" | "cannot_fulfil_delivery_area" | "pricing_error" | null;
  cancelDetails: string | null;
  cancelledAt: string | null;
  items: OrderDetailItem[];
}

/**
 * GET /api/v1/checkout/suppliers/{id}/cart -> Cart | null
 * POST /api/v1/checkout/suppliers/{id}/items -> Cart
 * PATCH /api/v1/checkout/suppliers/{id}/items/{productId} -> Cart
 * DELETE /api/v1/checkout/suppliers/{id}/items/{productId} -> Cart
 * POST /api/v1/checkout/suppliers/{id}/cart/clear -> Cart
 * GET /api/v1/checkout/carts -> { carts: Cart[] }
 * GET /api/v1/checkout/suppliers/{id}/history -> { orders: OrderHistoryEntry[] }
 * GET /api/v1/checkout/suppliers/{id}/history/{orderId} -> OrderDetail
 * POST /api/v1/checkout/suppliers/{id}/submit -> CheckoutResult
 */
