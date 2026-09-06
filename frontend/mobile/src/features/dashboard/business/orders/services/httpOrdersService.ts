import { apiDelete, apiGet, apiPatch, apiPost } from "@/services/api/apiClient";

import type { CancelReason, Cart, CheckoutResult, OrderDetail, OrderHistoryEntry, SubmitCheckoutRequest } from "../types";

export async function getCart(supplierId: string): Promise<Cart | null> {
  const result = await apiGet<Cart>(`/checkout/suppliers/${supplierId}/cart`);
  // apiGet's own shared helper (response.data?.data ?? {}) coalesces
  // a LEGITIMATE null response body -- exactly what get_supplier_cart
  // deliberately returns when no cart exists yet, see that route's
  // own docstring -- into an empty object, not null. A real, found
  // bug: CartScreen saw that empty object as truthy, skipped its own
  // empty-cart check, and crashed on cart.items.length since {} has
  // no items property. Restoring the real null here, rather than
  // changing the shared helper itself, which is used across the whole
  // app and could have a wider, harder-to-predict blast radius.
  if (!result || Object.keys(result).length === 0) return null;
  return result;
}

export async function getMyCarts(): Promise<Cart[]> {
  const data = await apiGet<{ carts: Cart[] }>("/checkout/carts");
  return data.carts;
}

export async function addItem(supplierId: string, productId: string, quantity: number): Promise<Cart> {
  return apiPost<Cart>(`/checkout/suppliers/${supplierId}/items`, { productId, quantity });
}

export async function updateItemQuantity(supplierId: string, productId: string, quantity: number): Promise<Cart> {
  return apiPatch<Cart>(`/checkout/suppliers/${supplierId}/items/${productId}`, { quantity });
}

export async function removeItem(supplierId: string, productId: string): Promise<Cart> {
  return apiDelete<Cart>(`/checkout/suppliers/${supplierId}/items/${productId}`);
}

export async function clearCart(supplierId: string): Promise<Cart> {
  return apiPost<Cart>(`/checkout/suppliers/${supplierId}/cart/clear`);
}

export async function getOrderHistory(supplierId: string): Promise<OrderHistoryEntry[]> {
  const data = await apiGet<{ orders: OrderHistoryEntry[] }>(`/checkout/suppliers/${supplierId}/history`);
  return data.orders;
}

export async function getOrderDetail(supplierId: string, orderId: string): Promise<OrderDetail> {
  return apiGet<OrderDetail>(`/checkout/suppliers/${supplierId}/history/${orderId}`);
}

/** PENDING_SUPPLIER_APPROVAL -> CANCELLED only -- see the backend's
 *  own cancellation_service.cancel_order_by_business for why a
 *  CONFIRMED order can't be self-cancelled here at all. */
export async function cancelOrder(
  supplierId: string,
  orderId: string,
  reason: CancelReason,
  details?: string
): Promise<{ id: string; orderReference: string; status: string }> {
  return apiPost(`/checkout/suppliers/${supplierId}/history/${orderId}/cancel`, { reason, details });
}

export async function submitCheckout(supplierId: string, request: SubmitCheckoutRequest): Promise<CheckoutResult> {
  return apiPost<CheckoutResult>(`/checkout/suppliers/${supplierId}/submit`, {
    paymentMethod: request.paymentMethod,
    deliveryType: request.deliveryType,
    deliveryAddressText: request.deliveryAddressText ?? null,
    deliveryBuilding: request.deliveryBuilding ?? null,
    deliveryStreet: request.deliveryStreet ?? null,
    deliverySuburb: request.deliverySuburb ?? null,
    deliveryCity: request.deliveryCity ?? null,
    deliveryProvince: request.deliveryProvince ?? null,
    deliveryPostalCode: request.deliveryPostalCode ?? null,
    deliveryLatitude: request.deliveryLatitude ?? null,
    deliveryLongitude: request.deliveryLongitude ?? null,
  });
}
