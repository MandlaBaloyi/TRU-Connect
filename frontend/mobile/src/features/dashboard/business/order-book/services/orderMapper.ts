/**
 * Order Book — money formatting/parsing and derived-value computation.
 * Same rules as loan-book/services/loanMapper.ts (kept as this feature's
 * own copy — see types.ts file docstring for why features stay
 * self-contained rather than cross-importing).
 *
 * SCREENS ORCHESTRATE, THEY DO NOT CALCULATE — every order total and
 * line total is computed here, once, never re-derived in a component.
 */

import type { Cents, CreateOrderLineItemInput, Order, OrderLineItem } from "../types";

/** "R 1 250.00" — full form, used wherever precision matters. */
export function formatCents(cents: Cents): string {
  const isNegative = cents < 0;
  const absolute = Math.abs(cents);
  const rands = Math.floor(absolute / 100);
  const remainder = absolute % 100;
  const grouped = rands.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return `${isNegative ? "-" : ""}R ${grouped}.${remainder.toString().padStart(2, "0")}`;
}

/** Compact form for tight spaces: "R 1 250" — drops cents when zero. */
export function formatCentsCompact(cents: Cents): string {
  if (cents % 100 === 0) {
    const rands = Math.floor(Math.abs(cents) / 100);
    const grouped = rands.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
    return `${cents < 0 ? "-" : ""}R ${grouped}`;
  }
  return formatCents(cents);
}

/**
 * Parse typed rands into integer cents. Accepts "48.50", "48,50" (comma
 * decimal, common locally), "R48.50", "1 250.00". Null on anything
 * unparseable so the caller shows a validation message rather than
 * silently recording a wrong amount.
 */
export function parseRandsToCents(input: string): Cents | null {
  const cleaned = input.replace(/[R\s]/gi, "").replace(",", ".").trim();
  if (cleaned.length === 0) return null;
  if (!/^\d*\.?\d*$/.test(cleaned)) return null;
  const rands = Number.parseFloat(cleaned);
  if (Number.isNaN(rands)) return null;
  return Math.round(rands * 100);
}

/** One line item's total. quantity is always a positive integer. */
export function calculateLineTotal(quantity: number, unitPrice: Cents): Cents {
  return Math.round(quantity) * unitPrice;
}

/** Builds real OrderLineItem rows (with ids + derived totals) from raw
 *  create-order input — the only place this composition happens. */
export function buildLineItems(
  items: CreateOrderLineItemInput[],
  generateId: (prefix: string) => string
): OrderLineItem[] {
  return items.map((item) => ({
    id: generateId("item"),
    description: item.description,
    quantity: item.quantity,
    unitPrice: item.unitPrice,
    lineTotal: calculateLineTotal(item.quantity, item.unitPrice),
  }));
}

/** An order's total — sum of its line items. Derived, never stored
 *  independently of its lines. */
export function calculateOrderTotal(lineItems: OrderLineItem[]): Cents {
  return lineItems.reduce((sum, item) => sum + item.lineTotal, 0);
}

/** Short human-facing reference — "#1024", never a raw id. */
export function formatOrderNumber(order: Pick<Order, "orderNumber">): string {
  return `#${order.orderNumber}`;
}

/** "3 × Big Kota, 1 × Small Kota" — an order's identity, derived from
 *  its actual items rather than a separate typed name. Truncates past
 *  two items ("+N more") so it stays a single readable line on the
 *  queue card. */
export function formatItemSummary(lineItems: OrderLineItem[]): string {
  if (lineItems.length === 0) return "";
  const parts = lineItems.map((item) => `${item.quantity} × ${item.description}`);
  if (parts.length <= 2) return parts.join(", ");
  return `${parts.slice(0, 2).join(", ")} +${parts.length - 2} more`;
}
