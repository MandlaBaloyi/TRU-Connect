/**
 * Real-backend implementation of the SAME functions loanBookApi.ts
 * already exports for the mock path -- see loanBookApi.ts for the
 * switch between them, driven by EXPO_PUBLIC_USE_MOCK_API.
 *
 * WHY THIS ISN'T A LoanRepository IMPLEMENTATION: LoanRepository was
 * built for MockDataRepository's own need to derive balances from raw
 * entries+payments held in memory. The real backend already does that
 * derivation once, correctly, using shared.finance (see
 * backend/src/domains/business/loan_book/services/loan_book_service.py)
 * -- re-deriving it a second time here would duplicate money logic in
 * two places with a real risk of the two silently disagreeing. This
 * file TRUSTS the backend's own numbers (outstandingAmount.minor_units,
 * amountPaid.minor_units) rather than recomputing them.
 *
 * What this file DOES still compute client-side: status labels
 * (OVERDUE/OUTSTANDING/PAID), day-counts, and aging buckets -- these are
 * genuinely display-only derivations, not money math, and reuse the
 * exact same already-tested pure functions the mock path uses
 * (agingCalculator.ts), fed by the backend's trusted amounts.
 */

import { apiGet, apiPost, apiDelete } from "@/services/api/apiClient";
import type {
  Customer,
  CustomerView,
  DeletedCustomerSummary,
  DeletedEntrySummary,
  LoanBookSummary,
  LoanEntry,
  LoanEntryView,
  LoanFilters,
  LoanHistoryEvent,
  Payment,
  RecordCreditSaleInput,
  RecordPaymentInput,
} from "../types";
import { determineStatus, calculateAgeInDays, calculateDaysOverdue } from "../algorithms/agingCalculator";
import { isExpiredFromTrash } from "../algorithms/trashRetention";
import { applyFilters } from "../services/loanFilters";

/**
 * Request deduplication -- collapses multiple near-simultaneous calls to
 * the SAME URL into ONE real network request, sharing the result.
 *
 * WHY THIS IS NEEDED HERE SPECIFICALLY: getLoanBookSummary(),
 * getLoanEntries(), and getCustomerViews() each independently fetch
 * /loan-book/customers. useLoanBook() calls all three via separate
 * useQuery hooks, which React Query fires in parallel on every screen
 * load -- three unrelated JS functions each blindly making their own
 * HTTP call to the identical endpoint. React Query's OWN built-in
 * deduplication only works across the SAME queryFn+queryKey; it can't
 * see that three DIFFERENT queryFns happen to call the same underlying
 * URL. This closes that gap directly, at the one place all three
 * ultimately share: the HTTP call itself.
 *
 * SHORT-LIVED BY DESIGN: the cache entry is removed the moment the
 * request settles (success OR failure), not kept around -- this is
 * ONLY collapsing genuinely-simultaneous in-flight requests, never
 * serving stale data. A fetch called a second later, after the first
 * one already resolved, hits the network fresh, exactly as before.
 * Verified: 3 simultaneous calls collapse to 1 network request; a call
 * made after the first one settles correctly fetches fresh, not cached.
 */
const inFlightRequests = new Map<string, Promise<unknown>>();

async function dedupedGet<T>(url: string): Promise<T> {
  const existing = inFlightRequests.get(url);
  if (existing) {
    return existing as Promise<T>;
  }
  const promise = apiGet<T>(url).finally(() => {
    inFlightRequests.delete(url);
  });
  inFlightRequests.set(url, promise);
  return promise as Promise<T>;
}

// --- Wire-format types (what the backend actually returns) --------------

interface MoneyDto {
  minor_units: number;
  currency: string;
  formatted: string;
}

interface CustomerDto {
  id: string;
  name: string;
  phone: string | null;
  firstRecordedAt: string;
  lastTransactionAt: string | null;
  deletedAt: string | null;
}

interface PaymentDto {
  id: string;
  amount: MoneyDto;
  paidAt: string;
  note: string | null;
}

interface LoanEntryDto {
  id: string;
  customerId: string;
  description: string | null;
  saleDate: string;
  isSettled: boolean;
  settledAt: string | null;
  originalAmount: MoneyDto;
  amountPaid: MoneyDto;
  outstandingAmount: MoneyDto;
  payments: PaymentDto[];
}

interface CustomerViewDto {
  customer: CustomerDto;
  entries: LoanEntryDto[];
  totalOutstanding: MoneyDto;
  openEntryCount: number;
}

interface HistoryEventDto {
  id: string;
  customerId: string;
  loanEntryId: string | null;
  eventType: string;
  amount: MoneyDto | null;
  description: string | null;
  reason: string | null;
  occurredAt: string;
}

// --- Mappers: backend DTO -> the exact frontend types screens expect ---

function mapCustomer(dto: CustomerDto): Customer {
  return {
    id: dto.id,
    name: dto.name,
    phone: dto.phone ?? undefined,
    firstRecordedAt: dto.firstRecordedAt,
    lastTransactionAt: dto.lastTransactionAt ?? undefined,
    deletedAt: dto.deletedAt ?? undefined,
  };
}

function mapPayment(dto: PaymentDto, loanEntryId: string): Payment {
  return {
    id: dto.id,
    loanEntryId,
    amount: dto.amount.minor_units, // TRUST the backend's number -- never re-derive
    paidAt: dto.paidAt,
    note: dto.note ?? undefined,
    createdAt: dto.paidAt,
  };
}

function mapLoanEntry(dto: LoanEntryDto): LoanEntry {
  return {
    id: dto.id,
    customerId: dto.customerId,
    originalAmount: dto.originalAmount.minor_units,
    saleDate: dto.saleDate,
    description: dto.description ?? undefined,
    isSettled: dto.isSettled,
    settledAt: dto.settledAt ?? undefined,
    createdAt: dto.saleDate,
    updatedAt: dto.saleDate,
  };
}

function mapEntryView(dto: LoanEntryDto): LoanEntryView {
  const entry = mapLoanEntry(dto);
  const payments = dto.payments.map((p) => mapPayment(p, dto.id));
  const outstandingAmount = dto.outstandingAmount.minor_units;
  const amountPaid = dto.amountPaid.minor_units;
  const ageInDays = calculateAgeInDays(entry);
  const daysOverdue = calculateDaysOverdue(entry, payments);
  const status = determineStatus(entry, payments);

  return { entry, payments, outstandingAmount, amountPaid, status, ageInDays, daysOverdue };
}

function mapCustomerView(dto: CustomerViewDto): CustomerView {
  const entries = dto.entries.map(mapEntryView);
  const totalOriginal = entries.reduce((sum, e) => sum + e.entry.originalAmount, 0);
  const sortedPaymentDates = entries
    .flatMap((e) => e.payments)
    .map((p) => p.paidAt)
    .sort();
  const lastPaymentAt = sortedPaymentDates[sortedPaymentDates.length - 1];
  return {
    customer: mapCustomer(dto.customer),
    entries,
    totalOutstanding: dto.totalOutstanding.minor_units,
    totalOriginal,
    openEntryCount: dto.openEntryCount,
    hasOverdue: entries.some((e) => e.status === "OVERDUE"),
    lastPaymentAt,
  };
}

function mapHistoryEvent(dto: HistoryEventDto): LoanHistoryEvent {
  return {
    id: dto.id,
    customerId: dto.customerId,
    loanEntryId: dto.loanEntryId ?? undefined,
    eventType: dto.eventType.toUpperCase() as LoanHistoryEvent["eventType"],
    amount: dto.amount?.minor_units,
    description: dto.description ?? undefined,
    reason: dto.reason ?? undefined,
    occurredAt: dto.occurredAt,
  };
}

// --- Public API — same signatures as the mock path in loanBookApi.ts ---

/**
 * Folds each STILL-ACTIVE customer's own non-expired trashed entries
 * back into their totalOutstanding — same fix and same reasoning as
 * getLoanBookSummary's, applied per-customer so the customer list and
 * a single customer's detail page agree with the top summary card
 * rather than each showing a different (and each individually wrong)
 * number. Deliberately does NOT add anything for a customer who is
 * themselves deleted — they're correctly absent from the active list
 * entirely, and Trash already shows their own totalOutstanding
 * correctly (computed backend-side including all their entries
 * regardless of entry-level deletion — see get_trash's customer
 * summaries, unaffected by this bug).
 */
function foldTrashedEntriesIntoViews(views: CustomerView[], trashedEntries: DeletedEntrySummary[], now: Date): CustomerView[] {
  const extraByCustomer = new Map<string, number>();
  trashedEntries.forEach((e) => {
    const deletedAt = e.view.entry.deletedAt;
    if (!deletedAt || isExpiredFromTrash(deletedAt, now)) return;
    const customerId = e.view.entry.customerId;
    extraByCustomer.set(customerId, (extraByCustomer.get(customerId) ?? 0) + e.view.outstandingAmount);
  });
  if (extraByCustomer.size === 0) return views;
  return views.map((view) => {
    const extra = extraByCustomer.get(view.customer.id);
    return extra ? { ...view, totalOutstanding: view.totalOutstanding + extra } : view;
  });
}

export async function getLoanBookSummary(): Promise<LoanBookSummary> {
  const [rawViews, trash] = await Promise.all([
    dedupedGet<CustomerViewDto[]>("/loan-book/customers"),
    getTrash(),
  ]);
  const now = new Date();

  // FIX: deleting a customer or entry with an unpaid balance must NOT
  // make that money vanish from "Money owed to you" — the debt is
  // still real and the item is still restorable for 7 days. Only once
  // something has actually aged out of Trash does it stop counting.
  // Without this, trashing a bad debt was an instant, silent way to
  // make outstanding totals look better without the debt actually
  // being resolved. See CustomerLoansScreen/TrashScreen for the
  // restore path this money returns through if undone.
  const customers = foldTrashedEntriesIntoViews(rawViews.map(mapCustomerView), trash.entries, now);
  const activeOutstanding = customers.reduce((sum, c) => sum + c.totalOutstanding, 0);
  const trashedCustomersOutstanding = trash.customers
    .filter((c) => c.customer.deletedAt && !isExpiredFromTrash(c.customer.deletedAt, now))
    .reduce((sum, c) => sum + c.totalOutstanding, 0);
  const totalOutstanding = activeOutstanding + trashedCustomersOutstanding;

  const customersOwingCount = customers.filter((c) => c.totalOutstanding > 0).length;
  const overdueCustomers = customers.filter((c) => c.hasOverdue);
  const overdueAmount = overdueCustomers.reduce(
    (sum, c) => sum + c.entries.filter((e) => e.status === "OVERDUE").reduce((s, e) => s + e.outstandingAmount, 0),
    0
  );
  const overdueCount = customers.reduce(
    (sum, c) => sum + c.entries.filter((e) => e.status === "OVERDUE").length,
    0
  );
  // "Collected in last 30 days" needs real payment history across all
  // entries; the customer-aggregate endpoint already carries every
  // entry's payments, so this is derived from that same response rather
  // than a second round-trip.
  const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000;
  const collectedLast30Days = customers
    .flatMap((c) => c.entries)
    .flatMap((e) => e.payments)
    .filter((p) => new Date(p.paidAt).getTime() >= thirtyDaysAgo)
    .reduce((sum, p) => sum + p.amount, 0);

  return { totalOutstanding, customersOwingCount, overdueCount, overdueAmount, collectedLast30Days };
}

export async function getLoanEntries(filters?: LoanFilters): Promise<LoanEntryView[]> {
  const dtos = await apiGet<LoanEntryDto[]>("/loan-book/entries");
  const views = dtos.map(mapEntryView);
  const customers = await listCustomers();
  return applyFilters(views, customers, filters);
}

export async function getLoanEntry(entryId: string): Promise<LoanEntryView | null> {
  try {
    const dto = await apiGet<LoanEntryDto>(`/loan-book/entries/${entryId}`);
    return mapEntryView(dto);
  } catch {
    return null; // 404 -- matches the mock path's "not found -> null" contract
  }
}

export async function getCustomerView(customerId: string): Promise<CustomerView | null> {
  try {
    const [dto, trash] = await Promise.all([
      apiGet<CustomerViewDto>(`/loan-book/customers/${customerId}`),
      getTrash(),
    ]);
    const [view] = foldTrashedEntriesIntoViews([mapCustomerView(dto)], trash.entries, new Date());
    return view;
  } catch {
    return null;
  }
}

export async function getCustomerViews(): Promise<CustomerView[]> {
  const [dtos, trash] = await Promise.all([
    dedupedGet<CustomerViewDto[]>("/loan-book/customers"),
    getTrash(),
  ]);
  return foldTrashedEntriesIntoViews(dtos.map(mapCustomerView), trash.entries, new Date());
}

export async function listCustomers(): Promise<Customer[]> {
  const dtos = await dedupedGet<CustomerViewDto[]>("/loan-book/customers");
  return dtos.map((v) => mapCustomer(v.customer));
}

export async function searchCustomers(term: string): Promise<Customer[]> {
  const all = await listCustomers();
  const needle = term.trim().toLowerCase();
  if (!needle) return [];
  return all.filter(
    (c) => c.name.toLowerCase().includes(needle) || (c.phone ?? "").includes(needle)
  );
}

export async function recordCreditSale(input: RecordCreditSaleInput): Promise<LoanEntryView> {
  let customerId = input.customerId;
  if (!customerId && input.newCustomerName) {
    const customer = await apiPost<CustomerDto>("/loan-book/customers", {
      name: input.newCustomerName,
      phone: input.newCustomerPhone,
    });
    customerId = customer.id;
  }
  const dto = await apiPost<LoanEntryDto>("/loan-book/entries", {
    customerId,
    amountCents: input.amount,
    description: input.description,
  });
  return mapEntryView(dto);
}

export async function recordPayment(input: RecordPaymentInput): Promise<LoanEntryView> {
  const dto = await apiPost<LoanEntryDto>(`/loan-book/entries/${input.loanEntryId}/payments`, {
    amountCents: input.amount,
    note: input.note,
  });
  return mapEntryView(dto);
}

export async function deleteLoanEntry(entryId: string, reason?: string): Promise<void> {
  await apiDelete(`/loan-book/entries/${entryId}`, { data: { reason } });
}

export async function restoreLoanEntry(entryId: string): Promise<void> {
  await apiPost(`/loan-book/entries/${entryId}/restore`);
}

export async function deleteCustomer(customerId: string, reason?: string): Promise<void> {
  await apiDelete(`/loan-book/customers/${customerId}`, { data: { reason } });
}

export async function restoreCustomer(customerId: string): Promise<void> {
  await apiPost(`/loan-book/customers/${customerId}/restore`);
}

export async function deletePayment(paymentId: string, entryId: string): Promise<LoanEntryView> {
  const dto = await apiDelete<LoanEntryDto>(`/loan-book/entries/${entryId}/payments/${paymentId}`);
  return mapEntryView(dto);
}

export async function getTrash(): Promise<{
  customers: DeletedCustomerSummary[];
  entries: DeletedEntrySummary[];
}> {
  const dto = await apiGet<{
    customers: (CustomerDto & { openEntryCount: number; totalEntryCount: number; totalOutstanding: MoneyDto })[];
    entries: { id: string; customerId: string; description: string | null; originalAmount: MoneyDto; deletionReason: string | null; deletedAt: string | null }[];
  }>("/loan-book/trash");

  const customers: DeletedCustomerSummary[] = dto.customers.map((c) => ({
    customer: mapCustomer(c),
    openEntryCount: c.openEntryCount,
    totalEntryCount: c.totalEntryCount,
    totalOutstanding: c.totalOutstanding.minor_units,
  }));

  // Trash entries come back from this endpoint as a lighter shape (no
  // payment history, since a trashed item's payments aren't shown in
  // the Trash list) -- wrapped into a full LoanEntryView with zero
  // payments so DeletedEntrySummary's shape matches exactly.
  const entries: DeletedEntrySummary[] = dto.entries.map((e) => {
    const entry: LoanEntry = {
      id: e.id,
      customerId: e.customerId,
      originalAmount: e.originalAmount.minor_units,
      saleDate: new Date().toISOString(),
      description: e.description ?? undefined,
      isSettled: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      deletionReason: e.deletionReason ?? undefined,
      deletedAt: e.deletedAt ?? undefined,
    };
    const view: LoanEntryView = {
      entry,
      payments: [],
      outstandingAmount: e.originalAmount.minor_units,
      amountPaid: 0,
      status: "OUTSTANDING",
      ageInDays: 0,
      daysOverdue: 0,
    };
    // customerName isn't included in the current backend response for
    // independently-trashed entries -- falls back to a placeholder
    // rather than guessing. Worth adding customerName to the backend's
    // trash response later so this matches the mock path exactly.
    return { view, customerName: "Customer" };
  });

  return { customers, entries };
}

export async function getLoanHistory(): Promise<LoanHistoryEvent[]> {
  const dtos = await apiGet<HistoryEventDto[]>("/loan-book/history");
  return dtos.map(mapHistoryEvent);
}

export async function recordReceiptEvent(
  _entryId: string,
  _customerId: string,
  _kind: "RECEIPT_VIEWED" | "RECEIPT_SHARED"
): Promise<void> {
  // Not yet wired to a real backend endpoint -- receipt view/share
  // events aren't recorded server-side yet (the backend's receipt
  // endpoint returns receipt DATA, but has no event-recording call from
  // the frontend wired to it). Fire-and-forget no-op for now rather than
  // erroring, matching the mock path's own "never breaks the UI" contract.
}