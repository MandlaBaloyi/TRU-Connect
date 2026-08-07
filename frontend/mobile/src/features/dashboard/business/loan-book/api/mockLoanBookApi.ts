/**
 * Loan Book — the ONLY boundary between this feature and its data.
 * Ref: feature spec ("All backend communication must happen ONLY through
 *      loanBookApi.ts. Never call fetch directly from Screens. Never call
 *      apiClient directly from Components.")
 *
 * WRITTEN AS THOUGH FLASK ALREADY EXISTS. Every function below has the
 * signature, argument shape, and return type it will have once the
 * backend is real — it simply happens to be satisfied by an in-memory
 * repository today. That is the entire point of building the UX first:
 * by the time the Flask endpoints get written (Sprint 3), the contract
 * they must satisfy has already been proven against real screens, so the
 * backend is built once rather than redesigned each time the UX moves.
 *
 * SWAPPING THE DATA SOURCE is a one-line change to `repository` below:
 *
 *      const repository: LoanRepository = new MockDataRepository();
 *      const repository: LoanRepository = new ApiRepository();
 *      const repository: LoanRepository = new OfflineRepository();
 *
 * No hook, screen, or component changes. That is the whole architecture.
 *
 * WHAT THIS FILE DOES BEYOND DELEGATING: it composes. A screen asking
 * for "the loan book" wants entries joined to payments joined to
 * customers, with balances derived and statuses resolved. Doing that
 * here — rather than in each hook — means the composition happens once
 * and identically everywhere.
 */
import type {
  Customer,
  CustomerView,
  DeletedCustomerSummary,
  DeletedEntrySummary,
  LoanBookSummary,
  LoanEntryView,
  LoanFilters,
  LoanHistoryEvent,
  Payment,
  RecordCreditSaleInput,
  RecordPaymentInput,
} from "../types";

import type { LoanRepository } from "./repository/LoanRepository";
import { MockDataRepository } from "./repository/MockDataRepository";
import {
  toCustomerView,
  toLoanBookSummary,
  toLoanEntryView,
  toLoanEntryViews,
} from "../services/loanMapper";
import { validatePayment } from "../algorithms/paymentAllocation";
import { validateCreditSale, normalisePhone } from "../services/loanValidation";
import { calculateOutstanding } from "../algorithms/balanceCalculator";
import { applyFilters } from "../services/loanFilters";

// ---------------------------------------------------------------------------
// THE SWAP POINT
// ---------------------------------------------------------------------------
const repository: LoanRepository = new MockDataRepository();

/**
 * Error type thrown by write operations that fail validation. Mirrors
 * the shape of ApiError (src/services/api/apiClient.ts) so screens
 * handling both look the same, and so swapping in the real API later
 * doesn't change any catch block.
 */
export class LoanBookError extends Error {
  code: string;
  fieldErrors: Record<string, string>;

  constructor(message: string, code: string, fieldErrors: Record<string, string> = {}) {
    super(message);
    this.name = "LoanBookError";
    this.code = code;
    this.fieldErrors = fieldErrors;
  }
}

/**
 * Client-generated ID.
 *
 * Deliberately generated on-device rather than by the server: it is what
 * makes offline creation possible without a round-trip, and it is
 * already the shape `client_generated_id` needs (Doc 04 §5.1 — "a
 * correctness requirement for offline sync, not an optimisation").
 * Adopting it now costs nothing and means the sync layer inherits it
 * rather than having to retrofit it.
 *
 * Uses crypto.randomUUID where available, falling back to a timestamped
 * random string — React Native's crypto support varies by version, and a
 * hard dependency on it would be an avoidable crash.
 */
function generateId(prefix: string): string {
  const globalCrypto = (globalThis as { crypto?: { randomUUID?: () => string } }).crypto;
  if (typeof globalCrypto?.randomUUID === "function") {
    return `${prefix}-${globalCrypto.randomUUID()}`;
  }
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

/**
 * Records one entry in the append-only history log.
 *
 * NEVER THROWS — matches the exact reasoning already established for
 * audit systems elsewhere in this project (src/shared/audit.py's
 * publish()): recording history must never break the action being
 * recorded. A lost history row is a real but survivable loss; a credit
 * sale failing to save because its OWN history entry failed to write
 * would be a much worse outcome.
 */
async function recordHistory(event: Omit<LoanHistoryEvent, "id" | "occurredAt">): Promise<void> {
  try {
    await repository.appendHistoryEvent({
      ...event,
      id: generateId("hist"),
      occurredAt: new Date().toISOString(),
    });
  } catch {
    // Swallowed deliberately — see docstring above.
  }
}

// ---------------------------------------------------------------------------
// Reads
// ---------------------------------------------------------------------------

/** Dashboard summary — the "what do I need to do right now" numbers. */
/**
 * Dashboard summary — the "what do I need to do right now" numbers.
 *
 * Deliberately uses listEntriesIncludingGracePeriod()/
 * listPaymentsIncludingGracePeriod(), NOT the plain active-only
 * listEntries()/listPayments() every browsable list uses. Deleting a
 * customer or entry is a decluttering action, reversible for 7 days —
 * the debt genuinely still exists and is still restorable the whole
 * time, so "Money owed to you" must keep counting it until it is
 * actually, permanently gone. See MockDataRepository's
 * listEntriesIncludingGracePeriod() docstring for the full story of the
 * bug this avoids.
 */
export async function getLoanBookSummary(): Promise<LoanBookSummary> {
  const [entries, payments] = await Promise.all([
    repository.listEntriesIncludingGracePeriod(),
    repository.listPaymentsIncludingGracePeriod(),
  ]);
  return toLoanBookSummary(entries, payments);
}

/**
 * The main list, filtered and sorted.
 *
 * NOTE: as of the customer-first redesign, no screen renders this list's
 * individual rows directly anymore — LoanBookScreen renders customers
 * (via getCustomerViews), and this function's only remaining consumer is
 * LoanAnalyticsScreen's statistics (aging buckets, credit-sale counts).
 * Since that's a REPORTING screen, not a browsable one, it correctly
 * uses the same grace-period-inclusive source as the summary above, so
 * the headline total and the breakdown beneath it never silently
 * disagree with each other.
 */
export async function getLoanEntries(filters?: LoanFilters): Promise<LoanEntryView[]> {
  const [entries, payments, customers] = await Promise.all([
    repository.listEntriesIncludingGracePeriod(),
    repository.listPaymentsIncludingGracePeriod(),
    repository.listCustomers(),
  ]);
  const views = toLoanEntryViews(entries, payments);
  return applyFilters(views, customers, filters);
}

/** One entry with its full payment history. */
export async function getLoanEntry(entryId: string): Promise<LoanEntryView | null> {
  const entry = await repository.getEntry(entryId);
  if (!entry) return null;
  const payments = await repository.listPaymentsForEntry(entryId);
  return toLoanEntryView(entry, payments);
}

/** One customer with all of their entries and totals. */
export async function getCustomerView(customerId: string): Promise<CustomerView | null> {
  const customer = await repository.getCustomer(customerId);
  if (!customer) return null;
  const [entries, payments] = await Promise.all([
    repository.listEntriesForCustomer(customerId),
    repository.listPayments(),
  ]);
  return toCustomerView(customer, entries, payments);
}

/** All customers, each with their outstanding total. */
export async function getCustomerViews(): Promise<CustomerView[]> {
  const [customers, entries, payments] = await Promise.all([
    repository.listCustomers(),
    repository.listEntries(),
    repository.listPayments(),
  ]);
  return customers
    .map((customer) => toCustomerView(customer, entries, payments))
    .sort((a, b) => b.totalOutstanding - a.totalOutstanding);
}

/** Plain customer list, for the picker on the record-sale screen. */
export async function listCustomers(): Promise<Customer[]> {
  return repository.listCustomers();
}

/**
 * Customer search by name or phone.
 *
 * Case- and format-insensitive: phone numbers are normalised on both
 * sides, so searching "082 123 4567" finds a customer stored as
 * "0821234567".
 */
export async function searchCustomers(term: string): Promise<Customer[]> {
  const customers = await repository.listCustomers();
  const needle = term.trim().toLowerCase();
  if (needle.length === 0) return customers;

  const needlePhone = normalisePhone(needle);
  return customers.filter((customer) => {
    const nameMatch = customer.name.toLowerCase().includes(needle);
    const phoneMatch = customer.phone
      ? normalisePhone(customer.phone).includes(needlePhone)
      : false;
    return nameMatch || phoneMatch;
  });
}

// ---------------------------------------------------------------------------
// Writes
// ---------------------------------------------------------------------------

/**
 * Record a credit sale — the core ≤30-second flow (Doc 06 §12.1).
 *
 * Creates the customer inline when `newCustomerName` is supplied, rather
 * than forcing a separate "add customer first" screen. Requiring a
 * detour mid-sale is exactly the friction Doc 02 §1.3 targets.
 */
export async function recordCreditSale(input: RecordCreditSaleInput): Promise<LoanEntryView> {
  const validation = validateCreditSale(input);
  if (!validation.isValid) {
    throw new LoanBookError("Please check the details.", "VALIDATION_FAILED", validation.errors);
  }

  const now = new Date().toISOString();
  let customerId = input.customerId;
  let isNewCustomer = false;

  if (!customerId && input.newCustomerName) {
    const customer: Customer = {
      id: generateId("cust"),
      name: input.newCustomerName.trim(),
      phone: input.newCustomerPhone ? normalisePhone(input.newCustomerPhone) : undefined,
      firstRecordedAt: now,
      lastTransactionAt: now,
    };
    await repository.createCustomer(customer);
    customerId = customer.id;
    isNewCustomer = true;
  }

  if (!customerId) {
    throw new LoanBookError("Choose a customer.", "CUSTOMER_REQUIRED", {
      customer: "Choose a customer or enter a name.",
    });
  }

  if (isNewCustomer) {
    await recordHistory({ customerId, eventType: "CUSTOMER_CREATED" });
  }

  const entry = await repository.createEntry({
    id: generateId("entry"),
    customerId,
    originalAmount: input.amount,
    saleDate: input.saleDate ?? now,
    description: input.description?.trim() || undefined,
    isSettled: false,
    createdAt: now,
    updatedAt: now,
  });

  await recordHistory({
    customerId,
    loanEntryId: entry.id,
    eventType: "SALE_CREATED",
    amount: entry.originalAmount,
    description: entry.description,
  });

  const existing = await repository.getCustomer(customerId);
  if (existing) {
    await repository.updateCustomer({ ...existing, lastTransactionAt: now });
  }

  return toLoanEntryView(entry, []);
}

/**
 * Record a repayment — the ≤15-second flow (Doc 06 §12.2).
 *
 * Validation runs against the DERIVED balance, not a stored column, so
 * an overpayment cannot slip through because a cached figure was stale.
 * On full settlement, is_settled/settled_at are written — matching what
 * the eventual Flask endpoint will do, so the contract stays honest.
 */
export async function recordPayment(input: RecordPaymentInput): Promise<LoanEntryView> {
  const entry = await repository.getEntry(input.loanEntryId);
  if (!entry) {
    throw new LoanBookError("That entry no longer exists.", "ENTRY_NOT_FOUND");
  }

  const existingPayments = await repository.listPaymentsForEntry(entry.id);
  const validation = validatePayment(entry, existingPayments, input.amount);
  if (!validation.isValid) {
    throw new LoanBookError(
      validation.message ?? "That payment amount isn't valid.",
      validation.reason ?? "VALIDATION_FAILED",
      { amount: validation.message ?? "" }
    );
  }

  const now = new Date().toISOString();
  const payment: Payment = {
    id: generateId("pay"),
    loanEntryId: entry.id,
    amount: input.amount,
    paidAt: input.paidAt ?? now,
    note: input.note?.trim() || undefined,
    createdAt: now,
  };
  await repository.createPayment(payment);
  await recordHistory({
    customerId: entry.customerId,
    loanEntryId: entry.id,
    eventType: "PAYMENT_RECORDED",
    amount: payment.amount,
  });

  const allPayments = [...existingPayments, payment];
  const outstanding = calculateOutstanding(entry, allPayments);

  const updated = await repository.updateEntry({
    ...entry,
    isSettled: outstanding === 0,
    settledAt: outstanding === 0 ? now : undefined,
    updatedAt: now,
  });

  const customer = await repository.getCustomer(entry.customerId);
  if (customer) {
    await repository.updateCustomer({ ...customer, lastTransactionAt: now });
  }

  return toLoanEntryView(updated, allPayments);
}

/**
 * Soft-delete an entry — moves it to Trash rather than erasing it (Doc
 * 06 §17: "Soft delete for ... Loan Book entries"). Doc 06 §12.3
 * explicitly allows correction and removal "because manual entry errors
 * are inevitable" — but an unlocked phone left open on the app is a real
 * risk too, so this is recoverable, not final. See
 * algorithms/trashRetention.ts for the recovery window and its honest
 * limitation (session-scoped until real persistence exists).
 */
export async function deleteLoanEntry(entryId: string, reason?: string): Promise<void> {
  const entry = await repository.getEntry(entryId);
  if (!entry) {
    throw new LoanBookError("That entry no longer exists.", "ENTRY_NOT_FOUND");
  }
  await repository.softDeleteEntry(entryId, reason);
  await recordHistory({
    customerId: entry.customerId,
    loanEntryId: entryId,
    eventType: "ENTRY_DELETED",
    reason,
  });
}

/** Restores a previously-deleted entry, if still within the retention
 *  window (repository.listDeletedEntries already excludes expired
 *  ones — this will fail with ENTRY_NOT_FOUND if called past that,
 *  since the entry has become unreachable, not literally erased). */
export async function restoreLoanEntry(entryId: string): Promise<void> {
  const entry = await repository.getEntry(entryId);
  // getEntry() only returns non-deleted rows, so a deleted-but-in-trash
  // entry won't be found there — check the trash list instead.
  const deleted = (await repository.listDeletedEntries()).find((e) => e.id === entryId);
  if (!entry && !deleted) {
    throw new LoanBookError("This entry can no longer be restored.", "ENTRY_NOT_FOUND");
  }
  await repository.restoreEntry(entryId);
  const restored = deleted ?? entry!;
  await recordHistory({
    customerId: restored.customerId,
    loanEntryId: entryId,
    eventType: "ENTRY_RESTORED",
  });
}

/**
 * Soft-delete a customer — cascades to their currently-open entries
 * (see MockDataRepository.softDeleteCustomer for the exact cascade
 * rule). Needed once a Loan Book has hundreds of customers and some
 * genuinely need cleaning up (duplicates, a business that closed, a
 * wrongly-created entry) — never an immediate, unrecoverable delete.
 */
export async function deleteCustomer(customerId: string, reason?: string): Promise<void> {
  const customer = await repository.getCustomer(customerId);
  if (!customer) {
    throw new LoanBookError("That customer no longer exists.", "CUSTOMER_NOT_FOUND");
  }
  await repository.softDeleteCustomer(customerId, reason);
  await recordHistory({ customerId, eventType: "CUSTOMER_DELETED", reason });
}

export async function restoreCustomer(customerId: string): Promise<void> {
  const deleted = (await repository.listDeletedCustomers()).find((c) => c.id === customerId);
  if (!deleted) {
    throw new LoanBookError("This customer can no longer be restored.", "CUSTOMER_NOT_FOUND");
  }
  await repository.restoreCustomer(customerId);
  await recordHistory({ customerId, eventType: "CUSTOMER_RESTORED" });
}

/** DeletedCustomerSummary / DeletedEntrySummary moved to types.ts, so
 *  both this file and httpLoanBookApi.ts share the exact same shape. */

/**
 * Everything currently sitting in Trash, correctly de-duplicated: one
 * row per deleted customer (covering all of their purchases), plus one
 * row per entry that was deleted independently while its own customer
 * remained active. See MockDataRepository.listDeletedEntries()'s
 * docstring for exactly why an entry belonging to a currently-deleted
 * customer never appears in the second list.
 */
export async function getTrash(): Promise<{
  customers: DeletedCustomerSummary[];
  entries: DeletedEntrySummary[];
}> {
  const [deletedCustomers, deletedEntries, payments, activeCustomers] = await Promise.all([
    repository.listDeletedCustomers(),
    repository.listDeletedEntries(),
    repository.listPayments(),
    repository.listCustomers(),
  ]);

  const nameById = new Map(activeCustomers.map((c) => [c.id, c.name]));

  const customerSummaries: DeletedCustomerSummary[] = await Promise.all(
    deletedCustomers.map(async (customer) => {
      const allEntries = await repository.listEntriesForCustomerIncludingDeleted(customer.id);
      const views = toLoanEntryViews(allEntries, payments);
      return {
        customer,
        openEntryCount: views.filter((v) => v.outstandingAmount > 0).length,
        totalEntryCount: views.length,
        totalOutstanding: views.reduce((sum, v) => sum + v.outstandingAmount, 0),
      };
    })
  );

  const entrySummaries: DeletedEntrySummary[] = deletedEntries.map((entry) => ({
    view: toLoanEntryView(entry, payments),
    customerName: nameById.get(entry.customerId) ?? "Unknown customer",
  }));

  return { customers: customerSummaries, entries: entrySummaries };
}

/** Remove a payment recorded in error. */
export async function deletePayment(paymentId: string, entryId: string): Promise<LoanEntryView> {
  const before = await repository.getEntry(entryId);
  const removedPayment = (await repository.listPaymentsForEntry(entryId)).find((p) => p.id === paymentId);
  await repository.deletePayment(paymentId);
  const entry = await repository.getEntry(entryId);
  if (!entry) {
    throw new LoanBookError("That entry no longer exists.", "ENTRY_NOT_FOUND");
  }
  const payments = await repository.listPaymentsForEntry(entryId);
  const outstanding = calculateOutstanding(entry, payments);
  const updated = await repository.updateEntry({
    ...entry,
    isSettled: outstanding === 0,
    settledAt: outstanding === 0 ? entry.settledAt : undefined,
    updatedAt: new Date().toISOString(),
  });
  if (removedPayment) {
    await recordHistory({
      customerId: entry.customerId,
      loanEntryId: entryId,
      eventType: "PAYMENT_REMOVED",
      amount: removedPayment.amount,
    });
  }
  return toLoanEntryView(updated, payments);
}

// ---------------------------------------------------------------------------
// History
// ---------------------------------------------------------------------------

/** The full Loan Book timeline — every sale, payment, deletion,
 *  restoration, and receipt interaction, newest first. */
export async function getLoanHistory(): Promise<LoanHistoryEvent[]> {
  return repository.listHistory();
}

/**
 * Records that a receipt was viewed or shared. Called from the screen,
 * fire-and-forget — a slow or failed history write must never delay or
 * block showing/sharing the receipt itself, matching recordHistory()'s
 * own "never throws" contract.
 */
export async function recordReceiptEvent(
  entryId: string,
  customerId: string,
  kind: "RECEIPT_VIEWED" | "RECEIPT_SHARED"
): Promise<void> {
  await recordHistory({ customerId, loanEntryId: entryId, eventType: kind });
}
