/**
 * Money formatting/parsing for Products.
 *
 * DUPLICATED FROM, NOT IMPORTED FROM, order-book/services/orderMapper.ts
 * -- matches this codebase's own established convention (Loan Book and
 * Order Book each carry their own copy rather than a shared cross-
 * feature utility; see useCurrentUserId.ts's docstring in either
 * feature for the same reasoning applied to a different concern).
 * Logic is identical on purpose: one South African money format across
 * the whole app, expressed once per feature rather than coupling
 * features to each other for it.
 */
import type { Cents } from "../types";

/**
 * "R 1 250.00" — South African convention uses a space as the
 * thousands separator, not a comma.
 */
export function formatCents(cents: Cents): string {
  const isNegative = cents < 0;
  const absolute = Math.abs(cents);
  const rands = Math.floor(absolute / 100);
  const remainder = absolute % 100;
  const grouped = rands.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return `${isNegative ? "-" : ""}R ${grouped}.${remainder.toString().padStart(2, "0")}`;
}

/**
 * Parse typed rands into integer cents. Accepts "12", "12.50", "12,50"
 * (comma decimal is common locally), "R12.50" — same acceptance rule
 * as order-book's own parser. Returns null (never throws) for anything
 * that isn't a plausible amount, so callers can turn that into a field
 * validation message rather than a crash.
 */
export function parseCentsInput(raw: string): Cents | null {
  const cleaned = raw.trim().replace(/^R\s*/i, "").replace(",", ".");
  if (cleaned === "") return null;
  if (!/^\d+(\.\d{1,2})?$/.test(cleaned)) return null;
  const rands = Number.parseFloat(cleaned);
  if (!Number.isFinite(rands) || rands < 0) return null;
  return Math.round(rands * 100);
}
