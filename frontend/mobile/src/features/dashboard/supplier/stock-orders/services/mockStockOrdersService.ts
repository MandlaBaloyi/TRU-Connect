import { ApiError } from "@/services/api/apiClient";

import type { CancelReason, DeclineReason, OrderDetail, OrderSummary, StockOrderStatus } from "../types";

const latency = (ms = 300) => new Promise<void>((resolve) => setTimeout(resolve, ms));

const hoursAgo = (h: number) => new Date(Date.now() - h * 3600_000).toISOString();
const daysAgo = (d: number) => new Date(Date.now() - d * 86_400_000).toISOString();

// Genuinely stateful across calls within this mock session -- approve/
// decline actually mutate this, same discipline as every other mock
// service in this app. Real orders across all three real states, so
// every tab has something believable to show, not just "New".
const orders = new Map<string, OrderDetail>([
  [
    "mock-order-1",
    {
      id: "mock-order-1",
      orderReference: "TRU-7QXM-4K9P2X",
      status: "PENDING_SUPPLIER_APPROVAL",
      totalCents: 24000,
      itemCount: 2,
      paymentMethod: "CASH",
      deliveryType: "DELIVER",
      submittedAt: hoursAgo(0.3),
      decidedAt: null,
      cancelledBy: null,
      cancelReason: null,
      cancelledAt: null,
      buyerName: "Mandla Zulu",
      buyerPhone: "+27821234567",
      buyerBusinessName: "Mandla's Spaza Shop",
      deliveryAddressText: "12 Church Street, Polokwane",
      buyerEmail: "mandla@example.com",
      declineReason: null,
      declineDetails: null,
      cancelDetails: null,
      items: [
        { productId: "p1", productName: "White Bread 700g", images: [], quantity: 10, priceCentsAtAddTime: 1800, lineTotalCents: 18000 },
        { productId: "p2", productName: "Full Cream Milk 1L", images: [], quantity: 3, priceCentsAtAddTime: 2000, lineTotalCents: 6000 },
      ],
    },
  ],
  [
    "mock-order-2",
    {
      id: "mock-order-2",
      orderReference: "TRU-7QXM-9R2WQZ",
      status: "PENDING_SUPPLIER_APPROVAL",
      totalCents: 58000,
      itemCount: 1,
      paymentMethod: "PROOF_OF_PAYMENT",
      deliveryType: "COLLECT",
      submittedAt: hoursAgo(28), // deliberately past the real 24h reminder threshold
      decidedAt: null,
      cancelledBy: null,
      cancelReason: null,
      cancelledAt: null,
      buyerName: "Naledi Mokoena",
      buyerPhone: "+27837654321",
      buyerBusinessName: "Naledi's Café",
      deliveryAddressText: "Provided by the supplier upon collection",
      buyerEmail: "naledi@example.com",
      declineReason: null,
      declineDetails: null,
      cancelDetails: null,
      items: [
        { productId: "p3", productName: "Cooking Oil 5L", images: [], quantity: 20, priceCentsAtAddTime: 2900, lineTotalCents: 58000 },
      ],
    },
  ],
  [
    "mock-order-3",
    {
      id: "mock-order-3",
      orderReference: "TRU-7QXM-2M8FRT",
      status: "CONFIRMED",
      totalCents: 15600,
      itemCount: 3,
      paymentMethod: "CASH",
      deliveryType: "DELIVER",
      submittedAt: daysAgo(1),
      decidedAt: hoursAgo(22), // approved a couple hours after submitting
      cancelledBy: null,
      cancelReason: null,
      cancelledAt: null,
      buyerName: "Sipho Dlamini",
      buyerPhone: "+27849876543",
      buyerBusinessName: "Sipho's Butchery",
      deliveryAddressText: "45 Market Road, Polokwane",
      buyerEmail: "sipho@example.com",
      declineReason: null,
      declineDetails: null,
      cancelDetails: null,
      items: [
        { productId: "p4", productName: "Sunflower Oil 2L", images: [], quantity: 6, priceCentsAtAddTime: 2600, lineTotalCents: 15600 },
      ],
    },
  ],
  [
    "mock-order-4",
    {
      id: "mock-order-4",
      orderReference: "TRU-7QXM-8H3KLP",
      status: "CONFIRMED",
      totalCents: 42000,
      itemCount: 1,
      paymentMethod: "PROOF_OF_PAYMENT",
      deliveryType: "COLLECT",
      submittedAt: daysAgo(6),
      decidedAt: daysAgo(5.8),
      cancelledBy: null,
      cancelReason: null,
      cancelledAt: null,
      buyerName: "Precious Ndlovu",
      buyerPhone: "+27827778899",
      buyerBusinessName: "Precious General Dealer",
      deliveryAddressText: "Provided by the supplier upon collection",
      buyerEmail: "precious@example.com",
      declineReason: null,
      declineDetails: null,
      cancelDetails: null,
      items: [
        { productId: "p5", productName: "Maize Meal 10kg", images: [], quantity: 12, priceCentsAtAddTime: 3500, lineTotalCents: 42000 },
      ],
    },
  ],
  [
    "mock-order-5",
    {
      id: "mock-order-5",
      orderReference: "TRU-7QXM-5N1QWD",
      status: "DECLINED",
      totalCents: 9800,
      itemCount: 2,
      paymentMethod: "CASH",
      deliveryType: "DELIVER",
      submittedAt: daysAgo(2),
      decidedAt: daysAgo(1.9),
      cancelledBy: null,
      cancelReason: null,
      cancelledAt: null,
      buyerName: "Blessing Mahlangu",
      buyerPhone: "+27835551234",
      buyerBusinessName: "Blessing's Tuck Shop",
      deliveryAddressText: "8 Voortrekker Street, Polokwane",
      buyerEmail: "blessing@example.com",
      declineReason: "out_of_stock",
      declineDetails: "Sold out this week, restocking Friday.",
      cancelDetails: null,
      items: [
        { productId: "p6", productName: "Rice 5kg", images: [], quantity: 4, priceCentsAtAddTime: 2450, lineTotalCents: 9800 },
      ],
    },
  ],
  [
    "mock-order-6",
    {
      id: "mock-order-6",
      orderReference: "TRU-7QXM-3T7YXB",
      status: "DECLINED",
      totalCents: 31200,
      itemCount: 1,
      paymentMethod: "PROOF_OF_PAYMENT",
      deliveryType: "COLLECT",
      submittedAt: daysAgo(9),
      decidedAt: daysAgo(8), // auto-declined roughly 24h after submission, never answered
      cancelledBy: null,
      cancelReason: null,
      cancelledAt: null,
      buyerName: "Tumi Radebe",
      buyerPhone: "+27823334455",
      buyerBusinessName: "Tumi's Corner Store",
      deliveryAddressText: "Provided by the supplier upon collection",
      buyerEmail: "tumi@example.com",
      // Auto-declined -- never actually answered.
      declineReason: "no_response",
      declineDetails: null,
      cancelDetails: null,
      items: [
        { productId: "p7", productName: "Washing Powder 3kg", images: [], quantity: 8, priceCentsAtAddTime: 3900, lineTotalCents: 31200 },
      ],
    },
  ],
]);

function withinRange(iso: string | null, from?: string, to?: string): boolean {
  if (!iso) return true;
  const t = new Date(iso).getTime();
  if (from && t < new Date(from).getTime()) return false;
  if (to && t > new Date(to).getTime()) return false;
  return true;
}

export async function getOrders(status?: StockOrderStatus, submittedFrom?: string, submittedTo?: string): Promise<OrderSummary[]> {
  await latency(300);
  const targetStatus: StockOrderStatus = status ?? "PENDING_SUPPLIER_APPROVAL";
  return Array.from(orders.values())
    .filter((o) => o.status === targetStatus)
    .filter((o) => withinRange(o.submittedAt, submittedFrom, submittedTo))
    .sort((a, b) => new Date(b.submittedAt ?? 0).getTime() - new Date(a.submittedAt ?? 0).getTime())
    .map(({ items, deliveryAddressText, declineDetails, ...summary }) => summary);
}

export async function getOrderDetail(orderId: string): Promise<OrderDetail> {
  await latency(300);
  const order = orders.get(orderId);
  if (!order) throw new ApiError("Order not found.", 404, [], "ORDER_NOT_FOUND");
  return order;
}

export async function approveOrder(orderId: string): Promise<OrderSummary> {
  await latency(400);
  const order = orders.get(orderId);
  if (!order) throw new ApiError("Order not found.", 404, [], "ORDER_NOT_FOUND");
  if (order.status !== "PENDING_SUPPLIER_APPROVAL") {
    throw new ApiError("This order has already been decided on.", 409, [], "ORDER_NOT_PENDING");
  }
  order.status = "CONFIRMED";
  return order;
}

export async function declineOrder(orderId: string, reason: DeclineReason, details?: string): Promise<OrderSummary> {
  await latency(400);
  const order = orders.get(orderId);
  if (!order) throw new ApiError("Order not found.", 404, [], "ORDER_NOT_FOUND");
  if (order.status !== "PENDING_SUPPLIER_APPROVAL") {
    throw new ApiError("This order has already been decided on.", 409, [], "ORDER_NOT_PENDING");
  }
  order.status = "DECLINED";
  order.declineReason = reason;
  order.declineDetails = details ?? null;
  return order;
}

/** CONFIRMED -> CANCELLED only -- mirrors the real backend's own
 *  cancel_order, a genuinely different door from decline above. */
export async function cancelOrder(orderId: string, reason: CancelReason, details?: string): Promise<OrderSummary> {
  await latency(400);
  const order = orders.get(orderId);
  if (!order) throw new ApiError("Order not found.", 404, [], "ORDER_NOT_FOUND");
  if (order.status !== "CONFIRMED") {
    throw new ApiError("Only a confirmed order can be cancelled this way.", 409, [], "ORDER_NOT_CONFIRMED");
  }
  order.status = "CANCELLED";
  order.cancelledBy = "supplier";
  order.cancelReason = reason;
  order.cancelDetails = details ?? null;
  order.cancelledAt = new Date().toISOString();
  return order;
}
