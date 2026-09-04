/**
 * supplier/stock-orders -- the supplier's own real actions on an
 * order: view what's pending, approve, decline. Communicates with
 * domains/supplier/stock_order_management on the backend
 * (/api/v1/supplier/stock-orders routes).
 */

export type PaymentMethod = "CASH" | "PROOF_OF_PAYMENT" | "PAYFAST";
export type DeliveryType = "DELIVER" | "COLLECT";
export type StockOrderStatus = "PENDING_SUPPLIER_APPROVAL" | "CONFIRMED" | "DECLINED";
export type SortOrder = "NEWEST" | "OLDEST";

/**
 * The real, structured decline reasons -- mirrors the backend's own
 * StockOrderDeclineReason exactly (which itself mirrors
 * SupplierReportReason's own shape: preset reasons plus a genuine
 * free-text escape hatch).
 */
export type DeclineReason =
  | "out_of_stock"
  | "cannot_fulfil_delivery_area"
  | "pricing_error"
  | "suspected_fraud"
  | "no_response"
  | "other";

export const DECLINE_REASON_LABELS: Record<DeclineReason, string> = {
  out_of_stock: "Out of stock",
  cannot_fulfil_delivery_area: "Can't fulfil this delivery area",
  pricing_error: "Pricing error",
  suspected_fraud: "Suspected fraud",
  // NOT a real, chosen-by-a-supplier reason -- set only by the
  // backend's own auto-decline sweep when an order sat unanswered
  // past the real, final timeout. Shown here so a Declined-tab card
  // for one of these reads honestly ("no response") rather than
  // falling back to a raw, ugly enum value.
  no_response: "No response in time",
  other: "Other",
};

export interface OrderSummary {
  id: string;
  orderReference: string;
  status: StockOrderStatus;
  totalCents: number;
  itemCount: number;
  paymentMethod: PaymentMethod | null;
  deliveryType: DeliveryType | null;
  submittedAt: string | null;
  buyerName: string | null;
  buyerPhone: string | null;
  buyerBusinessName: string | null;
  buyerEmail: string | null;
  /** Only meaningful when status is DECLINED -- included on the
   *  summary shape (not just OrderDetail) since the Declined tab's
   *  own cards show the real reason without a tap-through. */
  declineReason: DeclineReason | null;
}

export interface OrderDetailItem {
  productId: string;
  productName: string;
  images: string[];
  quantity: number;
  priceCentsAtAddTime: number;
  lineTotalCents: number;
}

export interface OrderDetail extends OrderSummary {
  deliveryAddressText: string | null;
  declineDetails: string | null;
  items: OrderDetailItem[];
}

/**
 * GET /api/v1/supplier/stock-orders -> { orders: OrderSummary[] }
 * GET /api/v1/supplier/stock-orders/{id} -> OrderDetail
 * POST /api/v1/supplier/stock-orders/{id}/approve -> OrderSummary
 * POST /api/v1/supplier/stock-orders/{id}/decline -> OrderSummary
 */
