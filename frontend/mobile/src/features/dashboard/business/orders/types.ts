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
  status: string;
  totalCents: number;
  itemCount: number;
  items: CartItem[];
}

export type PaymentMethod = "CASH" | "PROOF_OF_PAYMENT" | "PAYFAST";
export type DeliveryType = "DELIVER" | "COLLECT";

/**
 * The real status model, matching the backend's own StockOrderStatus
 * exactly. PENDING_SUPPLIER_APPROVAL is where CASH/PROOF_OF_PAYMENT
 * orders land -- neither is verified in real time, so the order
 * genuinely isn't settled yet. CONFIRMED is where a real PAYFAST
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

export interface OrderDetail {
  id: string;
  orderReference: string;
  status: string;
  totalCents: number;
  paymentMethod: PaymentMethod | null;
  deliveryType: DeliveryType | null;
  deliveryAddressText: string | null;
  submittedAt: string | null;
  /** Snapshotted at the real moment of submission -- what was true
   *  about this business then, not a live value that could have
   *  silently changed since. See the backend's own StockOrder model
   *  comment for the full reasoning. */
  buyerName: string | null;
  buyerPhone: string | null;
  buyerEmail: string | null;
  buyerBusinessName: string | null;
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
