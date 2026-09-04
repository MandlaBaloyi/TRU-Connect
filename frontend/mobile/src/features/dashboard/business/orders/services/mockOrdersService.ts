import { ApiError } from "@/services/api/apiClient";
import { getSupplierProduct } from "../../find-supplier/services/supplierSearchService";

import type { Cart, CartItem, CheckoutResult, OrderDetail, OrderHistoryEntry, SubmitCheckoutRequest } from "../types";

const latency = (ms = 300) => new Promise<void>((resolve) => setTimeout(resolve, ms));

// Ambiguous characters excluded (0/O, 1/I/L), matching the real
// backend's own generator exactly -- see that module's own docstring
// for why.
const REFERENCE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";

function randomReferenceChars(length: number): string {
  let result = "";
  for (let i = 0; i < length; i++) {
    result += REFERENCE_ALPHABET[Math.floor(Math.random() * REFERENCE_ALPHABET.length)];
  }
  return result;
}

/** A mock-realistic TRU-XXXX-XXXXXX reference -- the supplier "code"
 *  part is derived from the supplierId so it stays visually
 *  consistent across multiple orders to the same mock supplier,
 *  matching how the real backend's own code is assigned once and
 *  reused, not regenerated per order. Not cryptographically
 *  meaningful here -- this is mock data, not a real security
 *  boundary -- just shaped the same way. */
function generateMockOrderReference(supplierId: string): string {
  let hash = 0;
  for (let i = 0; i < supplierId.length; i++) {
    hash = (hash * 31 + supplierId.charCodeAt(i)) >>> 0;
  }
  let supplierCode = "";
  for (let i = 0; i < 4; i++) {
    supplierCode += REFERENCE_ALPHABET[hash % REFERENCE_ALPHABET.length];
    hash = Math.floor(hash / REFERENCE_ALPHABET.length);
  }
  return `TRU-${supplierCode}-${randomReferenceChars(6)}`;
}

// Keyed by supplierId -- one cart per supplier, matching the real
// backend's own "one CART per (business, supplier) pair" guarantee.
// Genuinely stateful across calls within this mock session, not a
// fixed fake response -- add/update/remove/checkout all actually
// mutate this.
const carts = new Map<string, Cart>();
const orderHistory = new Map<string, OrderHistoryEntry[]>();
const orderDetails = new Map<string, OrderDetail>();

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

export async function getOrderDetail(supplierId: string, orderId: string): Promise<OrderDetail> {
  await latency(300);
  const detail = orderDetails.get(orderId);
  if (!detail) throw new Error("Order not found.");
  return detail;
}

export async function submitCheckout(supplierId: string, request: SubmitCheckoutRequest): Promise<CheckoutResult> {
  await latency(500);
  const cart = carts.get(supplierId);
  if (!cart || cart.items.length === 0) throw new Error("Your cart is empty.");

  // PENDING_SUPPLIER_APPROVAL, matching the real backend's own status
  // model exactly -- CASH/PROOF_OF_PAYMENT are neither verified in
  // real time, so the order genuinely isn't settled the moment it's
  // placed.
  const status = "PENDING_SUPPLIER_APPROVAL";
  const orderReference = generateMockOrderReference(supplierId);

  const result: CheckoutResult = {
    id: cart.id,
    orderReference,
    status,
    totalCents: cart.totalCents,
    instructions:
      request.paymentMethod === "CASH"
        ? "Pay in cash on delivery or collection. The supplier will confirm your order shortly."
        : "Make your payment directly to the supplier, then send them your proof of payment.",
    redirectUrl: null,
  };

  const submittedAt = new Date().toISOString();
  const existingHistory = orderHistory.get(supplierId) ?? [];
  existingHistory.unshift({
    id: cart.id,
    orderReference,
    status,
    totalCents: cart.totalCents,
    itemCount: cart.itemCount,
    paymentMethod: request.paymentMethod,
    deliveryType: request.deliveryType,
    submittedAt,
  });
  orderHistory.set(supplierId, existingHistory);

  orderDetails.set(cart.id, {
    id: cart.id,
    orderReference,
    status,
    totalCents: cart.totalCents,
    paymentMethod: request.paymentMethod,
    deliveryType: request.deliveryType,
    deliveryAddressText: request.deliveryAddressText ?? null,
    submittedAt,
    // Real, mock-realistic buyer details -- this app's own established
    // mock business identity, matching what a real submission would
    // snapshot from the signed-in account.
    buyerName: "Mandla Zulu",
    buyerPhone: "+27 82 123 4567",
    buyerEmail: "mandla@example.com",
    buyerBusinessName: "Mandla's Spaza Shop",
    items: cart.items.map((item) => ({
      productId: item.productId,
      productName: item.productName,
      images: item.images,
      quantity: item.quantity,
      priceCentsAtAddTime: item.priceCentsAtAddTime,
      lineTotalCents: item.lineTotalCents,
    })),
  });

  // Real cart genuinely clears once submitted -- matches the real
  // backend's own "no active cart remains after submission" guarantee.
  carts.delete(supplierId);

  return result;
}
