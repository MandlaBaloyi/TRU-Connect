/**
 * Loan Book — in-memory repository backed by seed data.
 *
 * Phase 1 only. Satisfies the LoanRepository contract so that swapping
 * in an API- or SQLite-backed implementation later requires no change to
 * any hook, screen, or component.
 *
 * WHY THE ARTIFICIAL LATENCY: every method awaits a short delay before
 * resolving. A repository that returns instantly makes loading states
 * untestable and hides sluggish screens until real data arrives — at
 * which point the fix is a redesign rather than a tweak. Doc 02 §2.2
 * asks for cached-first paint and non-blocking first render; you can
 * only verify that against a data source that actually takes time.
 *
 * DATA RESETS ON RELOAD. That is deliberate for this phase: persistence
 * is the platform-wide offline engine's job, not this feature's. See the
 * feature README.
 *
 * SEED DATA is modelled on a real spaza shop's credit book — partial
 * repayments, round-number cash amounts, a few long-overdue debts, one
 * customer who always settles, one who has drifted. Realistic data
 * matters here: seeded with three tidy identical records, every screen
 * looks fine and no layout problem ever surfaces.
 */

import type { Customer, LoanEntry, LoanHistoryEvent, Payment } from "../../types";
import type { LoanRepository } from "./LoanRepository";
import { isExpiredFromTrash } from "../../algorithms/trashRetention";

/** Simulated I/O delay, ms. Long enough for loading states to be real,
 *  short enough not to make development tedious. */
const SIMULATED_LATENCY_MS = 220;

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), SIMULATED_LATENCY_MS));
}

function daysAgo(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString();
}

// ---------------------------------------------------------------------------
// Seed data
// ---------------------------------------------------------------------------

const SEED_CUSTOMERS: Customer[] = [
  {
    id: "cust-0001",
    name: "Mandla Baloyi",
    phone: "0821234567",
    firstRecordedAt: daysAgo(180),
    lastTransactionAt: daysAgo(3),
  },
  {
    id: "cust-0002",
    name: "Sipho Ndlovu",
    phone: "0739876543",
    firstRecordedAt: daysAgo(140),
    lastTransactionAt: daysAgo(12),
  },
  {
    // No phone — deliberately. Many customers are known by face only,
    // and every screen must handle a missing phone gracefully.
    id: "cust-0003",
    name: "Mama Grace",
    firstRecordedAt: daysAgo(95),
    lastTransactionAt: daysAgo(48),
  },
  {
    id: "cust-0004",
    name: "Gift Boss",
    phone: "0605551234",
    firstRecordedAt: daysAgo(75),
    lastTransactionAt: daysAgo(65),
  },
  {
    id: "cust-0005",
    name: "Nomsa Dlamini",
    phone: "0714445566",
    firstRecordedAt: daysAgo(30),
    lastTransactionAt: daysAgo(1),
  },
  {
    // Long name — checks truncation/wrapping on a 360dp screen (Doc 02 §2.1).
    id: "cust-0006",
    name: "Mkateko Mahlangu",
    phone: "0823334455",
    firstRecordedAt: daysAgo(60),
    lastTransactionAt: daysAgo(22),
  },
];

const SEED_ENTRIES: LoanEntry[] = [
  // mandla — reliable settler, one small open balance.
  {
    id: "entry-0001",
    customerId: "cust-0001",
    originalAmount: 24500, // R245.00
    saleDate: daysAgo(3),
    description: "Groceries",
    isSettled: false,
    createdAt: daysAgo(3),
    updatedAt: daysAgo(3),
  },
  {
    id: "entry-0002",
    customerId: "cust-0001",
    originalAmount: 18000,
    saleDate: daysAgo(35),
    description: "Bread and milk",
    isSettled: true,
    settledAt: daysAgo(28),
    createdAt: daysAgo(35),
    updatedAt: daysAgo(28),
  },
  {
    id: "entry-0003",
    customerId: "cust-0001",
    originalAmount: 32000,
    saleDate: daysAgo(70),
    isSettled: true,
    settledAt: daysAgo(64),
    createdAt: daysAgo(70),
    updatedAt: daysAgo(64),
  },
  {
    id: "entry-0004",
    customerId: "cust-0001",
    originalAmount: 15500,
    saleDate: daysAgo(110),
    isSettled: true,
    settledAt: daysAgo(102),
    createdAt: daysAgo(110),
    updatedAt: daysAgo(102),
  },

  //  — partially paid, now overdue.
  {
    id: "entry-0005",
    customerId: "cust-0002",
    originalAmount: 68000, // R680.00
    saleDate: daysAgo(52),
    description: "Monthly stock",
    isSettled: false,
    createdAt: daysAgo(52),
    updatedAt: daysAgo(12),
  },
  {
    id: "entry-0006",
    customerId: "cust-0002",
    originalAmount: 21000,
    saleDate: daysAgo(20),
    isSettled: false,
    createdAt: daysAgo(20),
    updatedAt: daysAgo(20),
  },

  // Mama Grace — long overdue, no payments at all.
  {
    id: "entry-0007",
    customerId: "cust-0003",
    originalAmount: 45000,
    saleDate: daysAgo(95),
    description: "Paraffin and candles",
    isSettled: false,
    createdAt: daysAgo(95),
    updatedAt: daysAgo(95),
  },

  //  — one very old unpaid debt.
  {
    id: "entry-0008",
    customerId: "cust-0004",
    originalAmount: 125000, // R1250.00 — largest single debt
    saleDate: daysAgo(75),
    description: "Building materials",
    isSettled: false,
    createdAt: daysAgo(75),
    updatedAt: daysAgo(65),
  },

  // Nomsa — brand new customer, recent, not yet due.
  {
    id: "entry-0009",
    customerId: "cust-0005",
    originalAmount: 9500,
    saleDate: daysAgo(1),
    description: "Airtime and snacks",
    isSettled: false,
    createdAt: daysAgo(1),
    updatedAt: daysAgo(1),
  },

  //  — several small entries, mixed.
  {
    id: "entry-0010",
    customerId: "cust-0006",
    originalAmount: 12000,
    saleDate: daysAgo(22),
    isSettled: false,
    createdAt: daysAgo(22),
    updatedAt: daysAgo(22),
  },
  {
    id: "entry-0011",
    customerId: "cust-0006",
    originalAmount: 8000,
    saleDate: daysAgo(40),
    isSettled: true,
    settledAt: daysAgo(33),
    createdAt: daysAgo(40),
    updatedAt: daysAgo(33),
  },
  {
    id: "entry-0012",
    customerId: "cust-0006",
    originalAmount: 30000,
    saleDate: daysAgo(58),
    description: "Party supplies",
    isSettled: false,
    createdAt: daysAgo(58),
    updatedAt: daysAgo(45),
  },
];

const SEED_PAYMENTS: Payment[] = [
  // mandla settles fully, promptly — round cash amounts.
  { id: "pay-0001", loanEntryId: "entry-0002", amount: 10000, paidAt: daysAgo(32), createdAt: daysAgo(32) },
  { id: "pay-0002", loanEntryId: "entry-0002", amount: 8000, paidAt: daysAgo(28), createdAt: daysAgo(28) },
  { id: "pay-0003", loanEntryId: "entry-0003", amount: 20000, paidAt: daysAgo(68), createdAt: daysAgo(68) },
  { id: "pay-0004", loanEntryId: "entry-0003", amount: 12000, paidAt: daysAgo(64), createdAt: daysAgo(64) },
  { id: "pay-0005", loanEntryId: "entry-0004", amount: 15500, paidAt: daysAgo(102), createdAt: daysAgo(102) },

  //  pays in pieces, then stops.
  { id: "pay-0006", loanEntryId: "entry-0005", amount: 20000, paidAt: daysAgo(40), createdAt: daysAgo(40) },
  { id: "pay-0007", loanEntryId: "entry-0005", amount: 15000, paidAt: daysAgo(12), note: "Part payment", createdAt: daysAgo(12) },

  //  paid once, long ago, then nothing.
  { id: "pay-0008", loanEntryId: "entry-0008", amount: 25000, paidAt: daysAgo(65), createdAt: daysAgo(65) },

  //  — one settled, one partially paid.
  { id: "pay-0009", loanEntryId: "entry-0011", amount: 8000, paidAt: daysAgo(33), createdAt: daysAgo(33) },
  { id: "pay-0010", loanEntryId: "entry-0012", amount: 10000, paidAt: daysAgo(45), createdAt: daysAgo(45) },
];

// ---------------------------------------------------------------------------
// Implementation
// ---------------------------------------------------------------------------
export class MockDataRepository implements LoanRepository {
  private customers: Customer[];
  private entries: LoanEntry[];
  private payments: Payment[];
  private history: LoanHistoryEvent[] = [];

  constructor() {
    this.customers = [...SEED_CUSTOMERS];
    this.entries = [...SEED_ENTRIES];
    this.payments = [...SEED_PAYMENTS];
  }

  // --- Customers ----------------------------------------------------

  async listCustomers(): Promise<Customer[]> {
    return delay(this.customers.filter((c) => !c.isDeleted));
  }

  async getCustomer(customerId: string): Promise<Customer | null> {
    const found = this.customers.find((c) => c.id === customerId);
    return delay(found && !found.isDeleted ? found : null);
  }

  async createCustomer(customer: Customer): Promise<Customer> {
    this.customers.push(customer);
    return delay(customer);
  }

  async updateCustomer(customer: Customer): Promise<Customer> {
    const index = this.customers.findIndex((c) => c.id === customer.id);
    if (index >= 0) this.customers[index] = customer;
    return delay(customer);
  }

  /**
   * Soft-deletes the customer AND cascades to their currently-open
   * entries — a customer and their purchase history aren't meaningfully
   * separable (deleting "Mandla" while three of her purchases stay
   * visible in other lists would be confusing, not useful).
   *
   * CASCADE RULE: only entries that are NOT already independently
   * deleted get swept in, and they're stamped with the SAME deletedAt
   * timestamp as the customer. That shared timestamp is what lets
   * restoreCustomer() restore exactly the entries it cascaded onto,
   * without accidentally reviving an entry someone deleted separately,
   * before or after this cascade.
   */
  async softDeleteCustomer(customerId: string, reason?: string): Promise<Customer> {
    const customer = this.customers.find((c) => c.id === customerId);
    if (!customer) throw new Error("Customer not found");

    const deletedAt = new Date().toISOString();
    customer.isDeleted = true;
    customer.deletedAt = deletedAt;
    customer.deletionReason = reason;

    for (const entry of this.entries) {
      if (entry.customerId === customerId && !entry.isDeleted) {
        entry.isDeleted = true;
        entry.deletedAt = deletedAt; // shared marker — see docstring
        entry.deletionReason = reason ? `Customer removed: ${reason}` : "Customer removed";
      }
    }

    return delay(customer);
  }

  async restoreCustomer(customerId: string): Promise<Customer> {
    const customer = this.customers.find((c) => c.id === customerId);
    if (!customer) throw new Error("Customer not found");

    const cascadeMarker = customer.deletedAt;
    customer.isDeleted = false;
    customer.deletedAt = undefined;
    customer.deletionReason = undefined;

    for (const entry of this.entries) {
      // Only restore entries stamped with the SAME deletion timestamp —
      // i.e. ones that went into trash as part of THIS cascade, not an
      // entry independently deleted at some other time.
      if (entry.customerId === customerId && entry.isDeleted && entry.deletedAt === cascadeMarker) {
        entry.isDeleted = false;
        entry.deletedAt = undefined;
        entry.deletionReason = undefined;
      }
    }

    return delay(customer);
  }

  async listDeletedCustomers(): Promise<Customer[]> {
    return delay(
      this.customers.filter((c) => c.isDeleted && c.deletedAt && !isExpiredFromTrash(c.deletedAt))
    );
  }

  // --- Entries ------------------------------------------------------

  async listEntries(): Promise<LoanEntry[]> {
    return delay(this.entries.filter((e) => !e.isDeleted));
  }

  async listEntriesForCustomer(customerId: string): Promise<LoanEntry[]> {
    return delay(this.entries.filter((e) => e.customerId === customerId && !e.isDeleted));
  }

  async getEntry(entryId: string): Promise<LoanEntry | null> {
    const found = this.entries.find((e) => e.id === entryId);
    return delay(found && !found.isDeleted ? found : null);
  }

  async createEntry(entry: LoanEntry): Promise<LoanEntry> {
    this.entries.push(entry);
    return delay(entry);
  }

  async updateEntry(entry: LoanEntry): Promise<LoanEntry> {
    const index = this.entries.findIndex((e) => e.id === entry.id);
    if (index >= 0) this.entries[index] = entry;
    return delay(entry);
  }

  async softDeleteEntry(entryId: string, reason?: string): Promise<LoanEntry> {
    const entry = this.entries.find((e) => e.id === entryId);
    if (!entry) throw new Error("Entry not found");
    entry.isDeleted = true;
    entry.deletedAt = new Date().toISOString();
    entry.deletionReason = reason;
    return delay(entry);
  }

  async restoreEntry(entryId: string): Promise<LoanEntry> {
    const entry = this.entries.find((e) => e.id === entryId);
    if (!entry) throw new Error("Entry not found");
    entry.isDeleted = false;
    entry.deletedAt = undefined;
    entry.deletionReason = undefined;
    return delay(entry);
  }

  /**
   * Deleted entries that deserve THEIR OWN row in Trash — meaning
   * their customer is NOT currently deleted. If the customer IS
   * deleted, every one of their entries (cascade-deleted alongside them
   * or independently deleted earlier) is already accounted for by that
   * customer's single trash row and its "N unpaid purchases" summary —
   * showing them again here would be the exact duplication problem
   * this method exists to avoid.
   *
   * This self-corrects on restore: restoreCustomer() only revives
   * entries that share its own cascade timestamp (see that method's
   * docstring), so an entry that was deleted independently, at a
   * different time, correctly reappears here on its own — with the
   * customer's name attached — the moment the customer becomes active
   * again.
   */
  async listDeletedEntries(): Promise<LoanEntry[]> {
    const deletedCustomerIds = new Set(this.customers.filter((c) => c.isDeleted).map((c) => c.id));
    return delay(
      this.entries.filter(
        (e) =>
          e.isDeleted &&
          e.deletedAt &&
          !isExpiredFromTrash(e.deletedAt) &&
          !deletedCustomerIds.has(e.customerId)
      )
    );
  }

  /** ALL entries for a customer — including ones currently soft-deleted
   *  — used only to build the Trash summary line ("3 unpaid purchases")
   *  for a deleted customer, since their normal entries are hidden from
   *  every other query while they sit in Trash. */
  async listEntriesForCustomerIncludingDeleted(customerId: string): Promise<LoanEntry[]> {
    return delay(this.entries.filter((e) => e.customerId === customerId));
  }

  // --- Payments -----------------------------------------------------

  async listPayments(): Promise<Payment[]> {
    const deletedEntryIds = new Set(this.entries.filter((e) => e.isDeleted).map((e) => e.id));
    return delay(this.payments.filter((p) => !deletedEntryIds.has(p.loanEntryId)));
  }

  async listPaymentsForEntry(entryId: string): Promise<Payment[]> {
    return delay(this.payments.filter((p) => p.loanEntryId === entryId));
  }

  async createPayment(payment: Payment): Promise<Payment> {
    this.payments.push(payment);
    return delay(payment);
  }

  async deletePayment(paymentId: string): Promise<void> {
    this.payments = this.payments.filter((p) => p.id !== paymentId);
    return delay(undefined);
  }

  // --- History (append-only) ------------------------------------------

  async appendHistoryEvent(event: LoanHistoryEvent): Promise<LoanHistoryEvent> {
    this.history.push(event);
    return delay(event);
  }

  async listHistory(): Promise<LoanHistoryEvent[]> {
    // Newest first — the natural reading order for a timeline.
    return delay(
      [...this.history].sort(
        (a, b) => new Date(b.occurredAt).getTime() - new Date(a.occurredAt).getTime()
      )
    );
  }

  // --- Grace-period-inclusive reads, for TOTALS ONLY -------------------

  /**
   * THE BUG THIS FIXES: deleting a customer/entry is a decluttering
   * action, reversible for 7 days — it was never meant to also mean
   * "this debt no longer exists." Before this method existed,
   * getLoanBookSummary() used the same active-only listEntries() the
   * browsable lists use, so "Money owed to you" dropped the instant
   * something was deleted, then silently disagreed with reality for up
   * to 7 real days (the debt still genuinely existed and was still
   * restorable) — and jumped back up if the item was later restored, or
   * simply stayed wrong forever if it wasn't. A number that moves for
   * reasons unrelated to a real financial event is exactly the kind of
   * inconsistency the derived-balance rule elsewhere in this file exists
   * to prevent.
   *
   * An entry's own deletedAt is authoritative regardless of whether it
   * was deleted directly or cascaded from a customer deletion (the
   * cascade stamps the SAME timestamp onto the entry — see
   * softDeleteCustomer) — so a single check here correctly covers both.
   */
  async listEntriesIncludingGracePeriod(): Promise<LoanEntry[]> {
    return delay(
      this.entries.filter((e) => !e.isDeleted || (e.deletedAt && !isExpiredFromTrash(e.deletedAt)))
    );
  }

  async listPaymentsIncludingGracePeriod(): Promise<Payment[]> {
    const permanentlyGoneEntryIds = new Set(
      this.entries
        .filter((e) => e.isDeleted && e.deletedAt && isExpiredFromTrash(e.deletedAt))
        .map((e) => e.id)
    );
    return delay(this.payments.filter((p) => !permanentlyGoneEntryIds.has(p.loanEntryId)));
  }
}
