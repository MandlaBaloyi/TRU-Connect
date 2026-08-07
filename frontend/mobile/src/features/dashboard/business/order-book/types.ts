/**
 * Order Book — domain types.
 * Ref: order_book_handoff.md (architecture) + TRU Connect master prompt
 *      (product scope: business-side customer order management).
 *
 * SCOPE BOUNDARY: this is record-keeping only, same discipline as Loan
 * Book. TRUConnect does not process payments here — an order's "total"
 * is what's owed, not money that has moved. Nothing in these types may
 * grow into a payments/checkout product.
 *
 * MONEY IS ALWAYS INTEGER CENTS, never a float — see loan-book/types.ts
 * for the full IEEE-754 rationale. Same rule, same reason, every feature.
 *
 * CUSTOMER IS SHARED WITH LOAN BOOK. The `Customer` shape here is
 * intentionally identical to loan-book/types.ts's Customer — same table,
 * same id space — but kept as this feature's own copy rather than a
 * cross-feature import, matching the existing convention where every
 * feature under dashboard/business/* is self-contained and only the
 * eventual backend enforces the single source of truth. When the real
 * API lands, both features' mappers point at the same `customers`
 * table and this duplication in types disappears naturally.
 *
 * KEPT DELIBERATELY SMALL: no product catalogue, no algorithms folder,
 * no analytics screen, no trash/soft-delete. Order Book's job is "record
 * an order, track it, complete or cancel it" — see decisions #6 in the
 * approved plan (simple structure, minimal lifecycle, free-text items).
 */

/** Integer cents. Never a float, never a formatted string. */
export type Cents = number;

/** ISO-8601 timestamp string, always UTC. */
export type IsoDateString = string;

/**
 * A customer of THIS business. Same canonical identity Loan Book uses —
 * see file-level docstring above.
 */
export interface Customer {
  id: string;
  name: string;
  phone?: string;
  /** Soft-delete marker. Present = sitting in Trash, permanently
   *  removed 7 days after this timestamp. Absent = active. */
  deletedAt?: IsoDateString;
}

/**
 * One line on an order. Free-text description only (no product
 * catalogue dependency) — decision #2 in the approved plan.
 */
export interface OrderLineItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: Cents;
  /** quantity * unitPrice. Derived, never hand-entered — see
   *  orderMapper.ts. Screens never compute this themselves. */
  lineTotal: Cents;
}

/**
 * MINIMAL LIFECYCLE — decision #3 in the approved plan.
 * Pending -> Completed, or Pending -> Cancelled. No intermediate states.
 * Deliberately absent: Confirmed/Preparing/Ready. If a real spec later
 * needs them, this is a colour-mapping + one enum change, not a rewrite
 * (same "safe default branch" discipline as LoanStatusBadge).
 */
export type OrderStatus = "PENDING" | "COMPLETED" | "CANCELLED";

/**
 * One customer order — the core record.
 */
export interface Order {
  id: string;
  customerId: string;
  /** Calendar date the order was created, "YYYY-MM-DD" — see
   *  orderNumber below for why this exists as its own field. */
  orderDate: string;
  /** Short human-facing reference, e.g. "#127" — never a raw UUID
   *  shown to the shop owner. UNIQUE ONLY WITHIN orderDate, not
   *  globally: numbering restarts at 1 every new day, so a busy shop
   *  never has to say "order fourteen thousand and six" out loud. The
   *  real identity of the row is `id` (a UUID); orderNumber+orderDate
   *  together are a display/lookup convenience, never a primary key —
   *  same separation the eventual `order_book_orders` table will use. */
  orderNumber: number;
  status: OrderStatus;
  lineItems: OrderLineItem[];
  /** Sum of all line totals. Derived, never stored/edited directly. */
  total: Cents;
  notes?: string;
  createdAt: IsoDateString;
  updatedAt: IsoDateString;
  completedAt?: IsoDateString;
  cancelledAt?: IsoDateString;
  cancellationReason?: string;

  /** Soft-delete marker — same 7-day Trash rule as Customer. An order
   *  can be trashed from any status (manual delete), or automatically
   *  once completed and past the auto-clear window. */
  deletedAt?: IsoDateString;
  deletedReason?: TrashReason;
}

/** Why something ended up in Trash — drives the label shown there. */
export type TrashReason = "MANUAL_DELETE" | "AUTO_CLEAR_COMPLETED" | "MANUAL_CLEAR_COMPLETED" | "AUTO_CLEAR_CANCELLED";

/** An Order joined with its customer — what screens actually render. */
export interface OrderView {
  order: Order;
  customer: Customer;
}

/** The Order Book queue summary — "what's outstanding right now". */
export interface OrderBookSummary {
  pendingCount: number;
  pendingValue: Cents;
  completedTodayCount: number;
}

/** Filters applied to the order list/queue. */
export interface OrderFilters {
  status?: OrderStatus;
  /** Free-text match against customer name/phone or order number. */
  searchTerm?: string;
}

// ---------------------------------------------------------------------------
// Write payloads — shaped as the eventual Flask request bodies
// ---------------------------------------------------------------------------

export interface CreateOrderLineItemInput {
  description: string;
  quantity: number;
  unitPrice: Cents;
}

export interface CreateOrderInput {
  /** Existing customer, or omit and supply newCustomerName to create one
   *  inline — same "never a separate screen first" rule as Loan Book's
   *  record-sale flow. */
  customerId?: string;
  newCustomerName?: string;
  newCustomerPhone?: string;
  items: CreateOrderLineItemInput[];
  notes?: string;
}

// ---------------------------------------------------------------------------
// Order Book History — an append-only event log, feature-scoped
// (same reasoning as LoanHistoryEvent: don't dump into a generic log,
// don't prematurely merge into shared.audit — see handoff doc §1, §7.4)
// ---------------------------------------------------------------------------

export type OrderHistoryEventType =
  | "ORDER_CREATED"
  | "ORDER_COMPLETED"
  | "ORDER_CANCELLED"
  | "CUSTOMER_CREATED";

export interface OrderHistoryEvent {
  id: string;
  customerId: string;
  /** Absent for customer-level events. */
  orderId?: string;
  eventType: OrderHistoryEventType;
  amount?: Cents;
  reason?: string;
  occurredAt: IsoDateString;
}

// ---------------------------------------------------------------------------
// Trash — soft-deleted orders and customers, 7-day recovery window
// ---------------------------------------------------------------------------

/** A trashed order, with the customer it belongs to already joined —
 *  same reasoning as OrderView, so TrashScreen never joins itself. */
export interface TrashedOrder {
  order: Order;
  customer: Customer;
  /** Days remaining before permanent deletion. Derived, never stored. */
  daysRemaining: number;
}

export interface TrashedCustomer {
  customer: Customer;
  daysRemaining: number;
}

// ---------------------------------------------------------------------------
// Balances — money made per day, and the auto-clear setting
// ---------------------------------------------------------------------------

/** One day's completed-order revenue. */
export interface DailyRevenueEntry {
  /** Calendar date this entry represents, "YYYY-MM-DD" — a plain date,
   *  not a timestamp, since a day's total isn't tied to a moment. */
  date: string;
  /** Sum of completed orders' totals for that day. */
  totalCents: Cents;
  orderCount: number;
}

/**
 * How long a completed order sits in the active queue before it's
 * automatically swept into Trash. "OFF" disables the sweep entirely —
 * the manual "Clear all completed" action is unaffected either way.
 */
/**
 * How long a completed or cancelled order sits in the active queue
 * before it's automatically moved to Trash. "OFF" disables it entirely.
 * "CUSTOM" means the shop owner typed their own hour count — see
 * AutoClearSetting.customHours. Presets kept SHORT on purpose (Off/5/15
 * min) — anything longer is what Custom is for, rather than growing
 * this list further.
 */
export type AutoClearDuration = "OFF" | "5_MIN" | "15_MIN" | "CUSTOM";

/** Fixed presets only — CUSTOM's window comes from customHours instead,
 *  see algorithms/autoClearSweep.ts's resolveWindowMs. */
export const AUTO_CLEAR_FIXED_DURATION_MS: Partial<Record<AutoClearDuration, number | null>> = {
  OFF: null,
  "5_MIN": 5 * 60 * 1000,
  "15_MIN": 15 * 60 * 1000,
};

export const AUTO_CLEAR_DURATION_LABELS: Record<AutoClearDuration, string> = {
  OFF: "Off",
  "5_MIN": "5 min",
  "15_MIN": "15 min",
  CUSTOM: "Custom",
};

/** The full setting, persisted together — customHours is only
 *  meaningful (and only sent) when duration is "CUSTOM". */
export interface AutoClearSetting {
  duration: AutoClearDuration;
  customHours?: number;
}

/** Which order status a given auto-clear setting applies to — completed
 *  and cancelled orders are cleared independently, with their own
 *  setting each, since a shop owner may want completed orders gone fast
 *  but keep cancelled ones around longer for reference (or vice versa). */
export type AutoClearScope = "COMPLETED" | "CANCELLED";

// ---------------------------------------------------------------------------
// Performance — the "View more balances" rollup, separate from the
// single TODAY figure shown on the main Balances screen.
// ---------------------------------------------------------------------------

export type PerformancePeriod = "3D" | "7D" | "30D" | "3M" | "1Y";

export const PERFORMANCE_PERIOD_LABELS: Record<PerformancePeriod, string> = {
  "3D": "3 Days",
  "7D": "7 Days",
  "30D": "30 Days",
  "3M": "3 Months",
  "1Y": "1 Year",
};

/** Calendar days each period covers, INCLUDING today — e.g. "3D" is
 *  today + the 2 days before it. Approximates months/years as fixed
 *  day counts, which is precise enough for a rollup like this. */
export const PERFORMANCE_PERIOD_DAYS: Record<PerformancePeriod, number> = {
  "3D": 3,
  "7D": 7,
  "30D": 30,
  "3M": 90,
  "1Y": 365,
};

export interface PerformanceStats {
  totalCents: Cents;
  orderCount: number;
  bestDayCents: Cents;
  averageDailyCents: Cents;
}
