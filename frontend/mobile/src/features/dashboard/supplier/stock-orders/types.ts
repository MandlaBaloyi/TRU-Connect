/**
 * supplier/stock-orders -- the supplier's own real actions on an
 * order: view what's pending, approve, decline. Communicates with
 * domains/supplier/stock_order_management on the backend
 * (/api/v1/supplier/stock-orders routes).
 */

// PaymentMethod is DEFINED ONCE, in dashboard/shared/payment. It used
// to be declared here AND in the other role's types.ts, identically --
// which is exactly how the backend ended up with a DIRECT value that
// three of five places had never heard of. Re-exported rather than
// moved so every existing import path keeps working.
import type { PaymentMethod } from "@/features/dashboard/shared/payment/paymentMethods";
export type { PaymentMethod };
export type DeliveryType = "DELIVER" | "COLLECT";
// CANCELLED included even though the backend's own model comment
// marks it "reserved, not reachable by anything in this pass" --
// StockOrderDetailScreen's own status display used to fall through
// an implicit else straight to "Declined" for anything that wasn't
// PENDING/CONFIRMED, which would have silently mislabeled a
// CANCELLED order the moment either-side cancellation becomes real.
// Cheap to widen the type correctly now rather than leave a latent
// bug for whoever builds that.
export type StockOrderStatus = "PENDING_SUPPLIER_APPROVAL" | "CONFIRMED" | "DECLINED" | "CANCELLED";
export type SortOrder = "NEWEST" | "OLDEST";

/** Supplier-facing phrasing, deliberately different from the
 *  business-side STATUS_LABELS in business/orders/types.ts -- "Pending
 *  YOUR decision" makes sense from a supplier's own point of view,
 *  "Pending supplier approval" doesn't read naturally there. The one
 *  place this domain's own status label text is decided, so no
 *  screen invents its own ternary chain (see StockOrderDetailScreen's
 *  own history with exactly that mistake). */
const STATUS_LABELS: Record<StockOrderStatus, string> = {
  PENDING_SUPPLIER_APPROVAL: "Pending your decision",
  CONFIRMED: "Confirmed",
  DECLINED: "Declined",
  CANCELLED: "Cancelled by business",
};

export function getStatusLabel(status: string): string {
  return STATUS_LABELS[status as StockOrderStatus] ?? status;
}

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
  /** Null while still PENDING_SUPPLIER_APPROVAL -- when this supplier
   *  actually approved or declined it. */
  decidedAt: string | null;
  buyerName: string | null;
  buyerPhone: string | null;
  buyerBusinessName: string | null;
  buyerEmail: string | null;
  /** Only meaningful when status is DECLINED -- included on the
   *  summary shape (not just OrderDetail) since the Declined tab's
   *  own cards show the real reason without a tap-through. */
  declineReason: DeclineReason | null;
  /** Only meaningful when status is CANCELLED. */
  cancelledBy: "business" | "supplier" | null;
  cancelReason: CancelReason | "changed_mind" | "found_alternative" | "ordered_by_mistake" | null;
  cancelledAt: string | null;
}

/** The real, enforced subset a SUPPLIER can choose from when
 *  cancelling an already-CONFIRMED order -- matches the backend's own
 *  SUPPLIER_CANCEL_REASONS in order_management_service.py exactly.
 *  Business-side reasons (changed_mind etc.) live in
 *  business/orders/types.ts's own CancelReason -- a genuinely
 *  different actor, not the same list reused. */
export type CancelReason = "out_of_stock" | "cannot_fulfil_delivery_area" | "pricing_error" | "other";

export const CANCEL_REASON_LABELS: Record<CancelReason, string> = {
  out_of_stock: "Out of stock",
  cannot_fulfil_delivery_area: "Can't fulfil this delivery area",
  pricing_error: "Pricing error",
  other: "Other reason",
};

/** For DISPLAYING a cancel reason regardless of which side set it --
 *  see business/orders/types.ts's own ANY_CANCEL_REASON_LABELS for
 *  the mirror image of this. */
export const ANY_CANCEL_REASON_LABELS: Record<string, string> = {
  ...CANCEL_REASON_LABELS,
  changed_mind: "Changed their mind",
  found_alternative: "Found it elsewhere",
  ordered_by_mistake: "Ordered by mistake",
};

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
  cancelDetails: string | null;
  items: OrderDetailItem[];
}

/**
 * GET /api/v1/supplier/stock-orders -> { orders: OrderSummary[] }
 * GET /api/v1/supplier/stock-orders/{id} -> OrderDetail
 * POST /api/v1/supplier/stock-orders/{id}/approve -> OrderSummary
 * POST /api/v1/supplier/stock-orders/{id}/decline -> OrderSummary
 */
