/**
 * Order Book — in-memory mock data source.
 * Ref: same "no repository abstraction folder needed for a feature this
 *      small" call as the backend decision — see order_book_handoff.md
 *      §2 for why algorithms/ was dropped once, applied here too: an
 *      extra repository/ layer would just wrap this same seed array
 *      with no second implementation yet to justify the indirection.
 *
 * WRITTEN AS THOUGH FLASK ALREADY EXISTS — every exported function has
 * the exact signature/shape it will have once httpOrderBookApi.ts is
 * real (Sprint 2 of this feature, after your review/approval of this
 * frontend). Swapping is a one-line change in orderBookApi.ts, no hook,
 * screen, or component changes — same architecture as Loan Book.
 *
 * SEED CUSTOMERS DELIBERATELY REUSE Loan Book's mock customer ids/names
 * (cust-0001 "Mandla Baloyi", etc.) rather than inventing new ones. This
 * is not a coincidence — it's rehearsing the real requirement (ONE
 * canonical `customers` table, shared with Loan Book) even in mock mode,
 * so a customer created in Loan Book's mock and one referenced here look
 * like the same person, the way they will for real once both features
 * point at the same backend table.
 */

import type {
  AutoClearScope,
  AutoClearSetting,
  Customer,
  CreateOrderInput,
  DailyRevenueEntry,
  Order,
  OrderBookSummary,
  OrderFilters,
  OrderHistoryEvent,
  OrderView,
  TrashedCustomer,
  TrashedOrder,
  TrashReason,
} from "../types";
import { buildLineItems, calculateOrderTotal } from "../services/orderMapper";
import { normalisePhone, validateCustomerName } from "../services/orderValidation";
import { daysRemainingInTrash, isExpiredFromTrash } from "../algorithms/trashRetention";
import { calculateDailyRevenue, toDateKey } from "../algorithms/dailyRevenue";
import { findOrdersDueForAutoClear } from "../algorithms/autoClearSweep";

/** Simulated I/O delay — long enough for loading states to be real,
 *  short enough not to be tedious. Matches Loan Book's mock latency. */
const SIMULATED_LATENCY_MS = 220;

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), SIMULATED_LATENCY_MS));
}

function generateId(prefix: string): string {
  const globalCrypto = (globalThis as { crypto?: { randomUUID?: () => string } }).crypto;
  if (typeof globalCrypto?.randomUUID === "function") {
    return `${prefix}-${globalCrypto.randomUUID()}`;
  }
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

function daysAgo(days: number, hours = 0): string {
  const date = new Date();
  date.setDate(date.getDate() - days);
  date.setHours(date.getHours() - hours);
  return date.toISOString();
}

export class OrderBookError extends Error {
  code: string;
  fieldErrors: Record<string, string>;

  constructor(message: string, code: string, fieldErrors: Record<string, string> = {}) {
    super(message);
    this.name = "OrderBookError";
    this.code = code;
    this.fieldErrors = fieldErrors;
  }
}

// ---------------------------------------------------------------------------
// Seed data — same customer identities as loan-book's mock, on purpose.
// ---------------------------------------------------------------------------

let customers: Customer[] = [
  { id: "cust-0001", name: "Mandla Baloyi", phone: "0821234567" },
  { id: "cust-0002", name: "Sipho Ndlovu", phone: "0739876543" },
  { id: "cust-0003", name: "Mama Grace" },
  { id: "cust-0004", name: "Gift Boss", phone: "0605551234" },
  { id: "cust-0005", name: "Nomsa Dlamini", phone: "0714445566" },
];

/** Per-day order numbering — see Order.orderNumber's docstring for why
 *  this resets every calendar day instead of growing forever. Seeded
 *  to match the highest number already used in the seed data below for
 *  each day, so the very next created order continues correctly. */
let dailyOrderCounters: Record<string, number> = {};

function nextDailyOrderNumber(dateKey: string): number {
  const current = dailyOrderCounters[dateKey] ?? 0;
  const next = current + 1;
  dailyOrderCounters[dateKey] = next;
  return next;
}

const todayKey = toDateKey(new Date().toISOString());
const yesterdayKey = toDateKey(daysAgo(1));

let orders: Order[] = [
  {
    id: "order-0001",
    customerId: "cust-0001",
    orderDate: todayKey,
    orderNumber: nextDailyOrderNumber(todayKey),
    status: "PENDING",
    lineItems: [
      { id: "item-0001", description: "2kg maize meal", quantity: 2, unitPrice: 3500, lineTotal: 7000 },
      { id: "item-0002", description: "Cooking oil 750ml", quantity: 1, unitPrice: 4500, lineTotal: 4500 },
    ],
    total: 11500,
    notes: "Collecting after 5pm",
    createdAt: daysAgo(0, 2),
    updatedAt: daysAgo(0, 2),
  },
  {
    id: "order-0005",
    customerId: "cust-0003",
    orderDate: todayKey,
    orderNumber: nextDailyOrderNumber(todayKey),
    status: "PENDING",
    lineItems: [
      { id: "item-0006", description: "Rice 5kg", quantity: 1, unitPrice: 12000, lineTotal: 12000 },
      { id: "item-0007", description: "Sugar 2kg", quantity: 1, unitPrice: 4200, lineTotal: 4200 },
      { id: "item-0008", description: "Candles pack", quantity: 2, unitPrice: 1500, lineTotal: 3000 },
    ],
    total: 19200,
    createdAt: daysAgo(0, 1),
    updatedAt: daysAgo(0, 1),
  },
  {
    id: "order-0003",
    customerId: "cust-0004",
    orderDate: todayKey,
    orderNumber: nextDailyOrderNumber(todayKey),
    status: "COMPLETED",
    lineItems: [{ id: "item-0004", description: "Bread x4, milk 2L", quantity: 1, unitPrice: 8900, lineTotal: 8900 }],
    total: 8900,
    createdAt: daysAgo(0, 3),
    updatedAt: daysAgo(0, 1),
    completedAt: daysAgo(0, 1),
  },
  {
    id: "order-0006",
    customerId: "cust-0005",
    orderDate: todayKey,
    orderNumber: nextDailyOrderNumber(todayKey),
    status: "COMPLETED",
    lineItems: [
      { id: "item-0009", description: "Big Kota", quantity: 3, unitPrice: 3000, lineTotal: 9000 },
      { id: "item-0010", description: "Small Kota", quantity: 1, unitPrice: 2000, lineTotal: 2000 },
    ],
    total: 11000,
    createdAt: daysAgo(0, 2),
    updatedAt: daysAgo(0, 0.5),
    completedAt: daysAgo(0, 0.5),
  },
  {
    id: "order-0004",
    customerId: "cust-0002",
    orderDate: yesterdayKey,
    orderNumber: nextDailyOrderNumber(yesterdayKey),
    status: "CANCELLED",
    lineItems: [{ id: "item-0005", description: "Phone case", quantity: 1, unitPrice: 6000, lineTotal: 6000 }],
    total: 6000,
    createdAt: daysAgo(1, 4),
    updatedAt: daysAgo(1, 1),
    cancelledAt: daysAgo(1, 1),
    cancellationReason: "Customer changed their mind",
  },
  {
    id: "order-0002",
    customerId: "cust-0001",
    orderDate: yesterdayKey,
    orderNumber: nextDailyOrderNumber(yesterdayKey),
    status: "COMPLETED",
    lineItems: [{ id: "item-0003", description: "Airtime voucher", quantity: 3, unitPrice: 1000, lineTotal: 3000 }],
    total: 3000,
    createdAt: daysAgo(1, 6),
    updatedAt: daysAgo(1, 5),
    completedAt: daysAgo(1, 5),
  },
];

/** Persisted settings — see hooks/useAutoClearSettings.ts for the
 *  AsyncStorage read/write; this module only holds the in-memory values
 *  the sweep function below reads from. Completed and cancelled orders
 *  clear independently — see AutoClearScope's docstring in types.ts. */
let autoClearSettingCompleted: AutoClearSetting = { duration: "OFF" };
let autoClearSettingCancelled: AutoClearSetting = { duration: "OFF" };

let historyEvents: OrderHistoryEvent[] = orders.map((order) => ({
  id: generateId("hist"),
  customerId: order.customerId,
  orderId: order.id,
  eventType: "ORDER_CREATED",
  amount: order.total,
  occurredAt: order.createdAt,
}));

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

async function recordHistory(event: Omit<OrderHistoryEvent, "id" | "occurredAt">): Promise<void> {
  try {
    historyEvents = [
      ...historyEvents,
      { ...event, id: generateId("hist"), occurredAt: new Date().toISOString() },
    ];
  } catch {
    // Never let history recording break the action being recorded —
    // same reasoning as Loan Book's recordHistory.
  }
}

function toOrderView(order: Order): OrderView | null {
  const customer = customers.find((candidate) => candidate.id === order.customerId);
  if (!customer) return null;
  return { order, customer };
}

function applyFilters(views: OrderView[], filters?: OrderFilters): OrderView[] {
  if (!filters) return views;
  let result = views;
  if (filters.status) {
    result = result.filter((view) => view.order.status === filters.status);
  }
  if (filters.searchTerm && filters.searchTerm.trim().length > 0) {
    const term = filters.searchTerm.trim().toLowerCase();
    result = result.filter(
      (view) =>
        view.customer.name.toLowerCase().includes(term) ||
        (view.customer.phone ?? "").includes(term) ||
        String(view.order.orderNumber).includes(term)
    );
  }
  return result;
}

// ---------------------------------------------------------------------------
// Reads
// ---------------------------------------------------------------------------

/** Orders sitting in Trash never appear in normal reads — same
 *  "soft-deleted rows are invisible to every ordinary query" rule Loan
 *  Book's trash follows. */
function activeOrders(): Order[] {
  return orders.filter((order) => !order.deletedAt);
}

function activeCustomers(): Customer[] {
  return customers.filter((customer) => !customer.deletedAt);
}

export async function getOrderBookSummary(): Promise<OrderBookSummary> {
  const pending = activeOrders().filter((order) => order.status === "PENDING");
  const startOfToday = new Date();
  startOfToday.setHours(0, 0, 0, 0);
  const completedToday = activeOrders().filter(
    (order) => order.status === "COMPLETED" && order.completedAt && new Date(order.completedAt) >= startOfToday
  );
  return delay({
    pendingCount: pending.length,
    pendingValue: pending.reduce((sum, order) => sum + order.total, 0),
    completedTodayCount: completedToday.length,
  });
}

export async function getOrders(filters?: OrderFilters): Promise<OrderView[]> {
  const views = activeOrders()
    .map(toOrderView)
    .filter((view): view is OrderView => view !== null)
    .sort((a, b) => new Date(b.order.createdAt).getTime() - new Date(a.order.createdAt).getTime());
  return delay(applyFilters(views, filters));
}

export async function getOrder(orderId: string): Promise<OrderView | null> {
  const order = orders.find((candidate) => candidate.id === orderId && !candidate.deletedAt);
  return delay(order ? toOrderView(order) : null);
}

export async function searchCustomers(term: string): Promise<Customer[]> {
  const trimmed = term.trim().toLowerCase();
  if (trimmed.length === 0) return delay([]);
  return delay(
    activeCustomers().filter(
      (customer) =>
        customer.name.toLowerCase().includes(trimmed) || (customer.phone ?? "").includes(trimmed)
    )
  );
}

// ---------------------------------------------------------------------------
// Trash — deleted orders and customers, 7-day recovery window
// ---------------------------------------------------------------------------

export async function getTrash(): Promise<{ orders: TrashedOrder[]; customers: TrashedCustomer[] }> {
  const now = new Date();

  const trashedOrders: TrashedOrder[] = orders
    .filter((order) => order.deletedAt && !isExpiredFromTrash(order.deletedAt, now))
    .map((order) => {
      const customer = customers.find((c) => c.id === order.customerId);
      if (!customer) return null;
      return { order, customer, daysRemaining: daysRemainingInTrash(order.deletedAt as string, now) };
    })
    .filter((entry): entry is TrashedOrder => entry !== null)
    .sort((a, b) => new Date(b.order.deletedAt as string).getTime() - new Date(a.order.deletedAt as string).getTime());

  const trashedCustomers: TrashedCustomer[] = customers
    .filter((customer) => customer.deletedAt && !isExpiredFromTrash(customer.deletedAt, now))
    .map((customer) => ({ customer, daysRemaining: daysRemainingInTrash(customer.deletedAt as string, now) }))
    .sort((a, b) => new Date(b.customer.deletedAt as string).getTime() - new Date(a.customer.deletedAt as string).getTime());

  return delay({ orders: trashedOrders, customers: trashedCustomers });
}

export async function deleteOrder(orderId: string, reason: TrashReason = "MANUAL_DELETE"): Promise<void> {
  const index = orders.findIndex((order) => order.id === orderId && !order.deletedAt);
  if (index === -1) throw new OrderBookError("Order not found.", "NOT_FOUND");
  const now = new Date().toISOString();
  orders = [
    ...orders.slice(0, index),
    { ...orders[index], deletedAt: now, deletedReason: reason },
    ...orders.slice(index + 1),
  ];
  return delay(undefined);
}

export async function restoreOrder(orderId: string): Promise<OrderView> {
  const index = orders.findIndex((order) => order.id === orderId && order.deletedAt);
  if (index === -1) throw new OrderBookError("Order not found in trash.", "NOT_FOUND");
  const restored: Order = { ...orders[index], deletedAt: undefined, deletedReason: undefined };
  orders = [...orders.slice(0, index), restored, ...orders.slice(index + 1)];
  const view = toOrderView(restored);
  if (!view) throw new OrderBookError("Could not restore order.", "UNKNOWN");
  return delay(view);
}

export async function deleteCustomer(customerId: string): Promise<void> {
  const index = customers.findIndex((customer) => customer.id === customerId && !customer.deletedAt);
  if (index === -1) throw new OrderBookError("Customer not found.", "NOT_FOUND");
  const now = new Date().toISOString();
  customers = [...customers.slice(0, index), { ...customers[index], deletedAt: now }, ...customers.slice(index + 1)];
  return delay(undefined);
}

export async function restoreCustomer(customerId: string): Promise<Customer> {
  const index = customers.findIndex((customer) => customer.id === customerId && customer.deletedAt);
  if (index === -1) throw new OrderBookError("Customer not found in trash.", "NOT_FOUND");
  const restored: Customer = { ...customers[index], deletedAt: undefined };
  customers = [...customers.slice(0, index), restored, ...customers.slice(index + 1)];
  return delay(restored);
}

/** Manual "Clear all completed" — moves every active completed order to
 *  Trash right now, regardless of the auto-clear setting. */
export async function clearAllCompletedNow(): Promise<{ clearedCount: number }> {
  const now = new Date().toISOString();
  let clearedCount = 0;
  orders = orders.map((order) => {
    if (order.status === "COMPLETED" && !order.deletedAt) {
      clearedCount += 1;
      return { ...order, deletedAt: now, deletedReason: "MANUAL_CLEAR_COMPLETED" as TrashReason };
    }
    return order;
  });
  return delay({ clearedCount });
}

/** Runs the auto-clear sweep for BOTH completed and cancelled orders
 *  against their own settings. Called from useAutoClearSweepRunner on
 *  app/queue open — see that hook and algorithms/autoClearSweep.ts's
 *  docstring for why the decision logic itself lives outside this file. */
export async function runAutoClearSweep(): Promise<{ clearedCount: number }> {
  const dueCompleted = findOrdersDueForAutoClear(activeOrders(), autoClearSettingCompleted, "COMPLETED");
  const dueCancelled = findOrdersDueForAutoClear(activeOrders(), autoClearSettingCancelled, "CANCELLED");
  const due = [...dueCompleted, ...dueCancelled];
  if (due.length === 0) return delay({ clearedCount: 0 });

  const dueCompletedIds = new Set(dueCompleted.map((order) => order.id));
  const now = new Date().toISOString();
  orders = orders.map((order) => {
    if (dueCompletedIds.has(order.id)) {
      return { ...order, deletedAt: now, deletedReason: "AUTO_CLEAR_COMPLETED" as TrashReason };
    }
    if (due.some((d) => d.id === order.id)) {
      return { ...order, deletedAt: now, deletedReason: "AUTO_CLEAR_CANCELLED" as TrashReason };
    }
    return order;
  });
  return delay({ clearedCount: due.length });
}

// ---------------------------------------------------------------------------
// Balances — daily revenue and the auto-clear settings
// ---------------------------------------------------------------------------

export async function getDailyRevenue(): Promise<DailyRevenueEntry[]> {
  return delay(calculateDailyRevenue(orders));
}

export async function getAutoClearSettings(): Promise<{ completed: AutoClearSetting; cancelled: AutoClearSetting }> {
  return delay({ completed: autoClearSettingCompleted, cancelled: autoClearSettingCancelled });
}

export async function setAutoClearSetting(scope: AutoClearScope, setting: AutoClearSetting): Promise<AutoClearSetting> {
  if (scope === "COMPLETED") {
    autoClearSettingCompleted = setting;
    return delay(autoClearSettingCompleted);
  }
  autoClearSettingCancelled = setting;
  return delay(autoClearSettingCancelled);
}

export async function getOrderHistory(): Promise<OrderHistoryEvent[]> {
  return delay(
    [...historyEvents].sort((a, b) => new Date(b.occurredAt).getTime() - new Date(a.occurredAt).getTime())
  );
}

// ---------------------------------------------------------------------------
// Writes
// ---------------------------------------------------------------------------

export async function createOrder(input: CreateOrderInput): Promise<OrderView> {
  if (input.items.length === 0) {
    throw new OrderBookError("Add at least one item.", "NO_ITEMS");
  }

  let customerId = input.customerId;

  if (!customerId) {
    const nameError = validateCustomerName(input.newCustomerName ?? "");
    if (nameError) {
      throw new OrderBookError(nameError, "INVALID_CUSTOMER_NAME", { newCustomerName: nameError });
    }
    const newCustomer: Customer = {
      id: generateId("cust"),
      name: input.newCustomerName!.trim(),
      phone: input.newCustomerPhone ? normalisePhone(input.newCustomerPhone) : undefined,
    };
    customers = [...customers, newCustomer];
    customerId = newCustomer.id;
    await recordHistory({ customerId, eventType: "CUSTOMER_CREATED" });
  }

  const lineItems = buildLineItems(input.items, generateId);
  const total = calculateOrderTotal(lineItems);
  const now = new Date().toISOString();
  const orderDate = toDateKey(now);

  const order: Order = {
    id: generateId("order"),
    customerId,
    orderDate,
    orderNumber: nextDailyOrderNumber(orderDate),
    status: "PENDING",
    lineItems,
    total,
    notes: input.notes?.trim() || undefined,
    createdAt: now,
    updatedAt: now,
  };

  orders = [order, ...orders];
  await recordHistory({ customerId, orderId: order.id, eventType: "ORDER_CREATED", amount: total });

  const view = toOrderView(order);
  if (!view) throw new OrderBookError("Could not create order.", "UNKNOWN");
  return delay(view);
}

export async function completeOrder(orderId: string): Promise<OrderView> {
  const index = orders.findIndex((order) => order.id === orderId);
  if (index === -1) throw new OrderBookError("Order not found.", "NOT_FOUND");
  const existing = orders[index];
  if (existing.status !== "PENDING") {
    throw new OrderBookError("Only pending orders can be completed.", "INVALID_TRANSITION");
  }
  const now = new Date().toISOString();
  const updated: Order = { ...existing, status: "COMPLETED", completedAt: now, updatedAt: now };
  orders = [...orders.slice(0, index), updated, ...orders.slice(index + 1)];
  await recordHistory({
    customerId: updated.customerId,
    orderId: updated.id,
    eventType: "ORDER_COMPLETED",
    amount: updated.total,
  });
  const view = toOrderView(updated);
  if (!view) throw new OrderBookError("Could not complete order.", "UNKNOWN");
  return delay(view);
}

export async function cancelOrder(orderId: string, reason?: string): Promise<OrderView> {
  const index = orders.findIndex((order) => order.id === orderId);
  if (index === -1) throw new OrderBookError("Order not found.", "NOT_FOUND");
  const existing = orders[index];
  if (existing.status !== "PENDING") {
    throw new OrderBookError("Only pending orders can be cancelled.", "INVALID_TRANSITION");
  }
  const now = new Date().toISOString();
  const updated: Order = {
    ...existing,
    status: "CANCELLED",
    cancelledAt: now,
    updatedAt: now,
    cancellationReason: reason?.trim() || undefined,
  };
  orders = [...orders.slice(0, index), updated, ...orders.slice(index + 1)];
  await recordHistory({
    customerId: updated.customerId,
    orderId: updated.id,
    eventType: "ORDER_CANCELLED",
    amount: updated.total,
    reason,
  });
  const view = toOrderView(updated);
  if (!view) throw new OrderBookError("Could not cancel order.", "UNKNOWN");
  return delay(view);
}
