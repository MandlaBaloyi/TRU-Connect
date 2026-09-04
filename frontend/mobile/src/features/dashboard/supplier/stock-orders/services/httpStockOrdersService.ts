import { apiGet, apiPost } from "@/services/api/apiClient";

import type { DeclineReason, OrderDetail, OrderSummary, StockOrderStatus } from "../types";

/** No status -> the real, unchanged "New" queue (pending only).
 *  A status -> the Approved/Declined tabs' own real history,
 *  optionally narrowed to a real date range. */
export async function getOrders(
  status?: StockOrderStatus,
  submittedFrom?: string,
  submittedTo?: string
): Promise<OrderSummary[]> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (submittedFrom) params.set("from", submittedFrom);
  if (submittedTo) params.set("to", submittedTo);
  const query = params.toString();
  const data = await apiGet<{ orders: OrderSummary[] }>(`/supplier/stock-orders${query ? `?${query}` : ""}`);
  return data.orders;
}

export async function getOrderDetail(orderId: string): Promise<OrderDetail> {
  return apiGet<OrderDetail>(`/supplier/stock-orders/${orderId}`);
}

export async function approveOrder(orderId: string): Promise<OrderSummary> {
  return apiPost<OrderSummary>(`/supplier/stock-orders/${orderId}/approve`);
}

export async function declineOrder(orderId: string, reason: DeclineReason, details?: string): Promise<OrderSummary> {
  return apiPost<OrderSummary>(`/supplier/stock-orders/${orderId}/decline`, { reason, details });
}
