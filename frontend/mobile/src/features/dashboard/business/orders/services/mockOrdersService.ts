import { ApiError } from "@/services/api/apiClient";
import { getSupplierProduct } from "../../find-supplier/services/supplierSearchService";

import type { Cart, CartItem, CheckoutResult, OrderHistoryEntry, SubmitCheckoutRequest } from "../types";

const latency = (ms = 300) => new Promise<void>((resolve) => setTimeout(resolve, ms));

// Keyed by supplierId -- one cart per supplier, matching the real
// backend's own "one CART per (business, supplier) pair" guarantee.
// Genuinely stateful across calls within this mock session, not a
// fixed fake response -- add/update/remove/checkout all actually
// mutate this.
const carts = new Map<string, Cart>();
const orderHistory = new Map<string, OrderHistoryEntry[]>();

function recalcTotals(cart: Cart): void {
  cart.items = cart.items.filter((item) => item.quantity > 0);
  cart.itemCount = cart.items.length;
  cart.totalCents = cart.items.reduce((sum, item) => sum + item.lineTotalCents, 0);
}

export async function getCart(supplierId: string): Promise<Cart | null> {
  await latency(200);
  return carts.get(supplierId) ?? null;
}

export async function getMyCarts(): Promise<Cart[]> {
  await latency(200);
  return Array.from(carts.values());
}

export async function addItem(supplierId: string, productId: string, quantity: number): Promise<Cart> {
  await latency(300);
  const product = await getSupplierProduct(supplierId, productId);
  if (!product) throw new Error("Product not found.");
  if (!product.inStock) {
    throw new ApiError(`${product.name} is currently out of stock.`, 409, [], "OUT_OF_STOCK", { productId });
  }

  let cart = carts.get(supplierId);
  if (!cart) {
    cart = {
      id: `mock-cart-${supplierId}`,
      supplierProfileId: supplierId,
      supplierName: product.supplierName,
      status: "CART",
      totalCents: 0,
      itemCount: 0,
      items: [],
    };
    carts.set(supplierId, cart);
  }

  const existing = cart.items.find((item) => item.productId === productId);
  if (existing) {
    existing.quantity += quantity;
    existing.lineTotalCents = existing.quantity * existing.priceCentsAtAddTime;
  } else {
    const newItem: CartItem = {
      productId,
      productName: product.name,
      images: product.images,
      quantity,
      priceCentsAtAddTime: product.priceCents,
      lineTotalCents: product.priceCents * quantity,
      isStale: false,
    };
    cart.items.push(newItem);
  }

  recalcTotals(cart);
  return cart;
}

export async function updateItemQuantity(supplierId: string, productId: string, quantity: number): Promise<Cart> {
  await latency(300);
  const cart = carts.get(supplierId);
  if (!cart) throw new Error("No cart exists for this supplier.");
  const item = cart.items.find((i) => i.productId === productId);
  if (!item) throw new Error("This product isn't in your cart.");
  item.quantity = quantity;
  item.lineTotalCents = item.quantity * item.priceCentsAtAddTime;
  recalcTotals(cart);
  return cart;
}

export async function removeItem(supplierId: string, productId: string): Promise<Cart> {
  await latency(300);
  const cart = carts.get(supplierId);
  if (!cart) throw new Error("No cart exists for this supplier.");
  cart.items = cart.items.filter((i) => i.productId !== productId);
  recalcTotals(cart);
  return cart;
}

export async function clearCart(supplierId: string): Promise<Cart> {
  await latency(300);
  const cart = carts.get(supplierId);
  if (!cart) throw new Error("No cart exists for this supplier.");
  cart.items = [];
  recalcTotals(cart);
  return cart;
}

export async function getOrderHistory(supplierId: string): Promise<OrderHistoryEntry[]> {
  await latency(300);
  return orderHistory.get(supplierId) ?? [];
}

export async function submitCheckout(supplierId: string, request: SubmitCheckoutRequest): Promise<CheckoutResult> {
  await latency(500);
  const cart = carts.get(supplierId);
  if (!cart || cart.items.length === 0) throw new Error("Your cart is empty.");

  const result: CheckoutResult = {
    id: cart.id,
    status: "SUBMITTED",
    totalCents: cart.totalCents,
    instructions:
      request.paymentMethod === "CASH"
        ? "Pay in cash on delivery or collection. The supplier will confirm your order shortly."
        : "Make your payment directly to the supplier, then send them your proof of payment.",
    redirectUrl: null,
  };

  const existingHistory = orderHistory.get(supplierId) ?? [];
  existingHistory.unshift({
    id: cart.id,
    status: "SUBMITTED",
    totalCents: cart.totalCents,
    itemCount: cart.itemCount,
    paymentMethod: request.paymentMethod,
    deliveryType: request.deliveryType,
    submittedAt: new Date().toISOString(),
  });
  orderHistory.set(supplierId, existingHistory);

  // Real cart genuinely clears once submitted -- matches the real
  // backend's own "no active cart remains after submission" guarantee.
  carts.delete(supplierId);

  return result;
}
