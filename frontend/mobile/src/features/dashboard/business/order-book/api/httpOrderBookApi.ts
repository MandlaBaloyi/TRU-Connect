/**
 * Order Book — real backend implementation. Same shape and same rules
 * as httpLoanBookApi.ts:
 *   - TRUST the backend's own numbers (minor_units), never re-derive
 *     money client-side
 *   - DTO interfaces match the backend's actual JSON exactly (read
 *     directly from backend/src/domains/business/order_book/api/
 *     order_book_routes.py's serialization functions, not guessed)
 *   - dedupedGet collapses simultaneous identical GETs the same way
 *     Loan Book's does
 *
 * CUSTOMER IS EMBEDDED IN EVERY ORDER RESPONSE, not fetched separately.
 * The backend's OrderView now carries `customer` inline (added
 * specifically so this file never has to guess at or fake a customer
 * name) — see order_book_service.py's OrderView dataclass.
 *
 * NOTE ON getOrderBookSummary(): the backend has no dedicated summary
 * endpoint. Mirrors Loan Book's own approach (getLoanBookSummary derives
 * from the customer list) — this derives the summary from a single
 * GET /order-book/orders call, same as the mock path derives it from
 * its in-memory array.
 */

import { apiGet, apiPost, apiDelete, apiPut, ApiError } from "@/services/api/apiClient";
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
  OrderLineItem,
  OrderStatus,
  OrderView,
  TrashedCustomer,
  TrashedOrder,
  TrashReason,
} from "../types";

// ---------------------------------------------------------------------------
// Request deduplication — same mechanism and same reasoning as Loan Book's.
// ---------------------------------------------------------------------------

const inFlightRequests = new Map<string, Promise<unknown>>();

async function dedupedGet<T>(url: string): Promise<T> {
  const existing = inFlightRequests.get(url);
  if (existing) return existing as Promise<T>;
  const promise = apiGet<T>(url).finally(() => inFlightRequests.delete(url));
  inFlightRequests.set(url, promise);
  return promise as Promise<T>;
}

// ---------------------------------------------------------------------------
// Wire-format types (what the backend actually returns)
// ---------------------------------------------------------------------------

interface MoneyDto {
  minor_units: number;
  currency: string;
  formatted: string;
}

interface LineItemDto {
  id: string;
  description: string;
  quantity: number;
  unitPrice: MoneyDto;
  lineTotal: MoneyDto;
}

interface CustomerDto {
  id: string;
  name: string;
  phone: string | null;
}

interface OrderDto {
  id: string;
  customerId: string;
  orderDate: string;
  orderNumber: number;
  status: "pending" | "completed" | "cancelled";
  total: MoneyDto;
  notes: string | null;
  createdAt: string;
  updatedAt: string;
  completedAt: string | null;
  cancelledAt: string | null;
  cancellationReason: string | null;
}

interface OrderViewDto extends OrderDto {
  customer: CustomerDto;
  lineItems: LineItemDto[];
}

interface TrashedOrderDto extends OrderDto {
  customer: CustomerDto;
  lineItems: LineItemDto[];
  daysRemaining: number;
}

interface TrashedCustomerDto extends CustomerDto {
  daysRemaining: number;
}

interface HistoryEventDto {
  id: string;
  customerId: string;
  orderId: string | null;
  eventType: string;
  amount: MoneyDto | null;
  reason: string | null;
  occurredAt: string;
}

interface AutoClearSettingDto {
  duration: "OFF" | "5_MIN" | "15_MIN" | "CUSTOM";
  customHours: number | null;
}

interface AutoClearSettingsDto {
  completed: AutoClearSettingDto;
  cancelled: AutoClearSettingDto;
}

// ---------------------------------------------------------------------------
// Mappers: backend DTO -> the exact frontend types screens expect
// ---------------------------------------------------------------------------

function mapLineItem(dto: LineItemDto): OrderLineItem {
  return {
    id: dto.id,
    description: dto.description,
    quantity: dto.quantity,
    unitPrice: dto.unitPrice.minor_units, // TRUST the backend — never re-derive
    lineTotal: dto.lineTotal.minor_units,
  };
}

function mapOrder(dto: OrderDto, lineItems: OrderLineItem[]): Order {
  return {
    id: dto.id,
    customerId: dto.customerId,
    orderDate: dto.orderDate,
    orderNumber: dto.orderNumber,
    status: dto.status.toUpperCase() as OrderStatus,
    lineItems,
    total: dto.total.minor_units,
    notes: dto.notes ?? undefined,
    createdAt: dto.createdAt,
    updatedAt: dto.updatedAt,
    completedAt: dto.completedAt ?? undefined,
    cancelledAt: dto.cancelledAt ?? undefined,
    cancellationReason: dto.cancellationReason ?? undefined,
  };
}

function mapCustomer(dto: CustomerDto): Customer {
  return { id: dto.id, name: dto.name, phone: dto.phone ?? undefined };
}

function mapOrderView(dto: OrderViewDto): OrderView {
  const lineItems = dto.lineItems.map(mapLineItem);
  return { order: mapOrder(dto, lineItems), customer: mapCustomer(dto.customer) };
}

function mapHistoryEvent(dto: HistoryEventDto): OrderHistoryEvent {
  return {
    id: dto.id,
    customerId: dto.customerId,
    orderId: dto.orderId ?? undefined,
    eventType: dto.eventType.toUpperCase() as OrderHistoryEvent["eventType"],
    amount: dto.amount?.minor_units,
    reason: dto.reason ?? undefined,
    occurredAt: dto.occurredAt,
  };
}

function mapAutoClearSetting(dto: AutoClearSettingDto): AutoClearSetting {
  return { duration: dto.duration, customHours: dto.customHours ?? undefined };
}

// ---------------------------------------------------------------------------
// Reads
// ---------------------------------------------------------------------------

export async function getOrderBookSummary(): Promise<OrderBookSummary> {
  const dtos = await dedupedGet<OrderViewDto[]>("/order-book/orders");
  const orders = dtos.map((dto) => mapOrder(dto, dto.lineItems.map(mapLineItem)));
  const pending = orders.filter((o) => o.status === "PENDING");
  const startOfToday = new Date();
  startOfToday.setHours(0, 0, 0, 0);
  const completedToday = orders.filter(
    (o) => o.status === "COMPLETED" && o.completedAt && new Date(o.completedAt) >= startOfToday
  );
  return {
    pendingCount: pending.length,
    pendingValue: pending.reduce((sum, o) => sum + o.total, 0),
    completedTodayCount: completedToday.length,
  };
}

export async function getOrders(filters?: OrderFilters): Promise<OrderView[]> {
  const params = new URLSearchParams();
  if (filters?.status) params.set("status", filters.status.toLowerCase());
  if (filters?.searchTerm) params.set("search", filters.searchTerm);
  const query = params.toString();
  const dtos = await apiGet<OrderViewDto[]>(`/order-book/orders${query ? `?${query}` : ""}`);
  return dtos.map(mapOrderView);
}

export async function getOrder(orderId: string): Promise<OrderView | null> {
  try {
    const dto = await apiGet<OrderViewDto>(`/order-book/orders/${orderId}`);
    return mapOrderView(dto);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function searchCustomers(term: string, signal?: AbortSignal): Promise<Customer[]> {
  if (!term.trim()) return [];
  const dtos = await apiGet<CustomerDto[]>(`/order-book/customers/search?term=${encodeURIComponent(term)}`, { signal });
  return dtos.map(mapCustomer);
}

export async function getOrderHistory(): Promise<OrderHistoryEvent[]> {
  const dtos = await apiGet<HistoryEventDto[]>("/order-book/history");
  return dtos.map(mapHistoryEvent);
}

// ---------------------------------------------------------------------------
// Writes
// ---------------------------------------------------------------------------

export async function createOrder(input: CreateOrderInput): Promise<OrderView> {
  const dto = await apiPost<OrderViewDto>("/order-book/orders", {
    customerId: input.customerId,
    newCustomerName: input.newCustomerName,
    newCustomerPhone: input.newCustomerPhone,
    items: input.items.map((item) => ({
      description: item.description,
      quantity: item.quantity,
      unitPriceCents: item.unitPrice,
    })),
    notes: input.notes,
  });
  return mapOrderView(dto);
}

export async function completeOrder(orderId: string): Promise<OrderView> {
  const dto = await apiPost<OrderViewDto>(`/order-book/orders/${orderId}/complete`);
  return mapOrderView(dto);
}

export async function cancelOrder(orderId: string, reason?: string): Promise<OrderView> {
  const dto = await apiPost<OrderViewDto>(`/order-book/orders/${orderId}/cancel`, { reason });
  return mapOrderView(dto);
}

export async function getTrash(): Promise<{ orders: TrashedOrder[]; customers: TrashedCustomer[] }> {
  const dto = await apiGet<{ orders: TrashedOrderDto[]; customers: TrashedCustomerDto[] }>("/order-book/trash");
  return {
    orders: dto.orders.map((o) => ({
      order: mapOrder(o, o.lineItems.map(mapLineItem)),
      customer: mapCustomer(o.customer),
      daysRemaining: o.daysRemaining,
    })),
    customers: dto.customers.map((c) => ({ customer: mapCustomer(c), daysRemaining: c.daysRemaining })),
  };
}

export async function deleteOrder(orderId: string, reason?: TrashReason): Promise<void> {
  await apiDelete(`/order-book/orders/${orderId}`, { data: { reason } });
}

export async function restoreOrder(orderId: string): Promise<OrderView> {
  const dto = await apiPost<OrderViewDto>(`/order-book/orders/${orderId}/restore`);
  return mapOrderView(dto);
}

export async function deleteCustomer(customerId: string): Promise<void> {
  await apiDelete(`/order-book/customers/${customerId}`);
}

export async function restoreCustomer(customerId: string): Promise<Customer> {
  const dto = await apiPost<CustomerDto>(`/order-book/customers/${customerId}/restore`);
  return mapCustomer(dto);
}

export async function clearAllCompletedNow(): Promise<{ clearedCount: number }> {
  return apiPost<{ clearedCount: number }>("/order-book/orders/clear-completed");
}

export async function runAutoClearSweep(): Promise<{ clearedCount: number }> {
  return apiPost<{ clearedCount: number }>("/order-book/balances/auto-clear-sweep");
}

export async function getDailyRevenue(): Promise<DailyRevenueEntry[]> {
  const dtos = await apiGet<{ date: string; totalCents: number; orderCount: number }[]>(
    "/order-book/balances/daily-revenue"
  );
  return dtos.map((d) => ({ date: d.date, totalCents: d.totalCents, orderCount: d.orderCount }));
}

export async function getAutoClearSettings(): Promise<{ completed: AutoClearSetting; cancelled: AutoClearSetting }> {
  const dto = await apiGet<AutoClearSettingsDto>("/order-book/balances/auto-clear-settings");
  return { completed: mapAutoClearSetting(dto.completed), cancelled: mapAutoClearSetting(dto.cancelled) };
}

export async function setAutoClearSetting(scope: AutoClearScope, setting: AutoClearSetting): Promise<AutoClearSetting> {
  const dto = await apiPut<AutoClearSettingsDto>("/order-book/balances/auto-clear-settings", {
    scope,
    duration: setting.duration,
    customHours: setting.customHours,
  });
  return mapAutoClearSetting(scope === "COMPLETED" ? dto.completed : dto.cancelled);
}
