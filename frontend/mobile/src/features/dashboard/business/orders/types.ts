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

export interface SubmitCheckoutRequest {
  paymentMethod: PaymentMethod;
  deliveryType: DeliveryType;
  deliveryAddressText?: string | null;
}

export interface CheckoutResult {
  id: string;
  status: string;
  totalCents: number;
  instructions: string | null;
  redirectUrl: string | null;
}

export interface OrderHistoryEntry {
  id: string;
  status: string;
  totalCents: number;
  itemCount: number;
  paymentMethod: PaymentMethod | null;
  deliveryType: DeliveryType | null;
  submittedAt: string | null;
}

/**
 * GET /api/v1/checkout/suppliers/{id}/cart -> Cart | null
 * POST /api/v1/checkout/suppliers/{id}/items -> Cart
 * PATCH /api/v1/checkout/suppliers/{id}/items/{productId} -> Cart
 * DELETE /api/v1/checkout/suppliers/{id}/items/{productId} -> Cart
 * POST /api/v1/checkout/suppliers/{id}/cart/clear -> Cart
 * GET /api/v1/checkout/carts -> { carts: Cart[] }
 * GET /api/v1/checkout/suppliers/{id}/history -> { orders: OrderHistoryEntry[] }
 * POST /api/v1/checkout/suppliers/{id}/submit -> CheckoutResult
 */
