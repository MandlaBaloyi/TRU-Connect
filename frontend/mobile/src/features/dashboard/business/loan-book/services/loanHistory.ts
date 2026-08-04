/**
 * Loan Book — history/timeline display logic. PURE.
 *
 * Turns a raw LoanHistoryEvent into what the timeline screen actually
 * renders: a plain-language line, an icon hint, and day-grouping. Kept
 * separate from receiptService.ts/loanMapper.ts since this is a distinct
 * concern (describing an EVENT, not a LOAN).
 */

import type { LoanHistoryEvent, LoanHistoryEventType } from "../types";
import { formatCents } from "./loanMapper";
import { daysSince } from "../algorithms/agingCalculator";

/** Plain-language description of one event, e.g. "Sold Groceries" /
 *  "Payment received" / "Entry removed" (Doc 02 §14: jargon-free). */
export function describeHistoryEvent(event: LoanHistoryEvent): string {
  switch (event.eventType) {
    case "SALE_CREATED":
      return event.description ? `Sold ${event.description}` : "Credit sale recorded";
    case "PAYMENT_RECORDED":
      return "Payment received";
    case "PAYMENT_REMOVED":
      return "Payment removed";
    case "ENTRY_DELETED":
      return "Entry removed";
    case "ENTRY_RESTORED":
      return "Entry restored";
    case "CUSTOMER_CREATED":
      return "New customer added";
    case "CUSTOMER_DELETED":
      return "Customer removed";
    case "CUSTOMER_RESTORED":
      return "Customer restored";
    case "RECEIPT_VIEWED":
      return "Receipt viewed";
    case "RECEIPT_SHARED":
      return "Receipt shared";
    default:
      // Exhaustiveness guard, same defensive-default pattern as
      // LoanStatusBadge: a future event type this screen doesn't know
      // about yet still renders something legible.
      return String(event.eventType);
  }
}

/** Whether this event type represents removing/undoing something —
 *  drives icon/colour choice on the timeline. */
export function isNegativeEvent(eventType: LoanHistoryEventType): boolean {
  return eventType === "ENTRY_DELETED" || eventType === "CUSTOMER_DELETED" || eventType === "PAYMENT_REMOVED";
}

export function isRestorativeEvent(eventType: LoanHistoryEventType): boolean {
  return eventType === "ENTRY_RESTORED" || eventType === "CUSTOMER_RESTORED";
}

/** One day's worth of events, for the "Today / Yesterday / Monday"
 *  grouped timeline layout. */
export interface HistoryDayGroup {
  /** "Today", "Yesterday", or a weekday/date label. */
  label: string;
  events: LoanHistoryEvent[];
}

function dayLabelFor(occurredAt: string, now: Date): string {
  const days = daysSince(occurredAt, now);
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) {
    return new Date(occurredAt).toLocaleDateString("en-ZA", { weekday: "long" });
  }
  return new Date(occurredAt).toLocaleDateString("en-ZA", { day: "numeric", month: "long" });
}

/**
 * Groups events (already expected newest-first) into day buckets without
 * re-sorting — the caller controls ordering; this only labels and
 * partitions by calendar day.
 */
export function groupHistoryByDay(events: LoanHistoryEvent[], now: Date = new Date()): HistoryDayGroup[] {
  const groups: HistoryDayGroup[] = [];

  for (const event of events) {
    const label = dayLabelFor(event.occurredAt, now);
    const lastGroup = groups[groups.length - 1];
    if (lastGroup && lastGroup.label === label) {
      lastGroup.events.push(event);
    } else {
      groups.push({ label, events: [event] });
    }
  }

  return groups;
}

/** Amount label for an event, when relevant — blank for events with no
 *  associated money (e.g. CUSTOMER_RESTORED). */
export function historyEventAmountLabel(event: LoanHistoryEvent): string | undefined {
  return event.amount !== undefined ? formatCents(event.amount) : undefined;
}

// ---------------------------------------------------------------------------
// Transaction History — the bank-statement-style subset of the full log
// ---------------------------------------------------------------------------

/**
 * The event types that count as a "transaction" for the customer-facing
 * Transaction History screen — a real movement of money, the same scope
 * a bank statement shows. Everything else the log records (deletions,
 * restores, receipt views/shares) stays in the underlying append-only
 * log for the "complete lending history" scaling goal, but doesn't
 * belong on a screen whose whole premise is "what money moved, and
 * when" — a business owner reading a bank statement never sees "card
 * deleted" or "statement viewed" mixed in with their transactions.
 */
export const TRANSACTION_EVENT_TYPES: readonly LoanHistoryEventType[] = [
  "SALE_CREATED",
  "PAYMENT_RECORDED",
  "PAYMENT_REMOVED",
];

export function isTransactionEvent(eventType: LoanHistoryEventType): boolean {
  return (TRANSACTION_EVENT_TYPES as LoanHistoryEventType[]).includes(eventType);
}

/** Filters a full event list down to just the transaction subset,
 *  preserving whatever order the caller already sorted it in. */
export function filterTransactionEvents(events: LoanHistoryEvent[]): LoanHistoryEvent[] {
  return events.filter((event) => isTransactionEvent(event.eventType));
}

/**
 * Short type label for the transaction row — "Loan", "Payment", "Payment
 * removed". Deliberately "Loan" here, not "Purchase": this is the shop
 * owner's own internal ledger/statement, never shown to the customer, so
 * it's the right place for the plain word they actually think in — the
 * "Purchase" wording elsewhere in this feature exists specifically to
 * avoid implying TRU Connect lends money on documents that could reach
 * the customer (the receipt); a private transaction-type label in the
 * owner's own statement carries no such risk.
 */
export function transactionTypeLabel(eventType: LoanHistoryEventType): string {
  switch (eventType) {
    case "SALE_CREATED":
      return "Loan";
    case "PAYMENT_RECORDED":
      return "Payment";
    case "PAYMENT_REMOVED":
      return "Payment removed";
    default:
      return String(eventType);
  }
}

/**
 * Colour tone for a transaction row. Money coming IN (a payment) is
 * POSITIVE; a payment being reversed is ATTENTION; a loan simply being
 * recorded is NEUTRAL — recording a sale isn't good or bad news, it's
 * just a fact, so it gets no colour emphasis (same restraint already
 * applied to InsightList's neutral-tone dots).
 */
export function transactionTone(eventType: LoanHistoryEventType): "POSITIVE" | "ATTENTION" | "NEUTRAL" {
  switch (eventType) {
    case "PAYMENT_RECORDED":
      return "POSITIVE";
    case "PAYMENT_REMOVED":
      return "ATTENTION";
    default:
      return "NEUTRAL";
  }
}
