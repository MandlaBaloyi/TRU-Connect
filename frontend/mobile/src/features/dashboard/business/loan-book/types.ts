/**
 * Loan Book — domain types.
 * Ref: docs/04_DATABASE_DESIGN.txt §3.4–3.6 (business_customers,
 *      credit_ledger_entries, credit_ledger_payments)
 *      docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt §12 (Loan Book Lifecycle)
 *
 * These names deliberately mirror the eventual PostgreSQL tables so the
 * frontend contract and the Flask schema cannot drift apart. When the
 * backend is built (Sprint 3), loanMapper.ts is the only file that has
 * to know the wire format differs (snake_case ↔ camelCase).
 *
 * SCOPE BOUNDARY (Doc 04 §3.5): this is record-keeping only. TRUConnect
 * does not lend, does not hold funds, does not collect, and charges no
 * interest. It replaces a paper credit book. Nothing in these types may
 * grow into a lending product.
 *
 * MONEY IS ALWAYS INTEGER CENTS (Doc 04 §9.1: "All monetary values use
 * fixed-point decimal, never floating point"). JavaScript numbers are
 * IEEE-754 doubles, so 0.1 + 0.2 !== 0.3 — storing rands as floats would
 * mean a customer's balance silently drifting by fractions of a cent
 * across repeated part-payments. Every amount below is cents as a whole
 * number; formatting to "R 48.20" happens only at the display edge.
 */

/** Integer cents. Never a float, never a formatted string. */
export type Cents = number;

/** ISO-8601 timestamp string, always UTC. */
export type IsoDateString = string;

/**
 * A customer of THIS business who buys on credit.
 *
 * NOT a TRU Connect user — these are the shop's neighbours and
 * walk-ins, people who have never heard of the platform. Doc 04 §3.4 is
 * explicit that this is "deliberately minimal -- this is not a CRM".
 * Resist adding fields here; every extra field is typing the shop owner
 * has to do while serving someone (Doc 02 §1.2).
 */
export interface Customer {
  /** Client-generated UUID. Generated on-device so a customer can be
   *  added with no connectivity and no server round-trip — required for
   *  the ≤30s record-a-sale target, and already the shape the eventual
   *  `client_generated_id` sync key needs. */
  id: string;
  name: string;
  /** Optional by design (Doc 04 §3.4). Many informal customers are known
   *  by name and face only; requiring a phone number would block the
   *  entry entirely. */
  phone?: string;
  firstRecordedAt: IsoDateString;
  lastTransactionAt?: IsoDateString;
  /** Soft-delete, matching the backend's BaseModel convention
   *  (created_at/updated_at/is_deleted/deleted_at) exactly, so this
   *  shape needs no translation once a real API sits behind it. Deleting
   *  a customer cascades to their entries — see
   *  api/repository/MockDataRepository.ts's softDeleteCustomer for the
   *  exact cascade/restore semantics. */
  isDeleted?: boolean;
  deletedAt?: IsoDateString;
  deletionReason?: string;
}

/**
 * One credit sale — money a customer owes this business.
 * Maps to business.credit_ledger_entries.
 */
export interface LoanEntry {
  id: string;
  customerId: string;
  /** What the sale was worth when it happened. Immutable. */
  originalAmount: Cents;
  saleDate: IsoDateString;
  description?: string;
  isSettled: boolean;
  settledAt?: IsoDateString;
  createdAt: IsoDateString;
  updatedAt: IsoDateString;
  /** Soft-delete — see Customer.isDeleted for the shared rationale.
   *  "Manual entry errors are inevitable" (Doc 06 §12.3) is exactly why
   *  this can never be an immediate, unrecoverable delete: a business
   *  owner who fat-fingers a removal, or someone else who picks up an
   *  unlocked phone, must be able to undo it. */
  isDeleted?: boolean;
  deletedAt?: IsoDateString;
  deletionReason?: string;
}

/**
 * A repayment against one entry. Partial repayment is fully supported —
 * Doc 06 §12.3: "this is how informal credit actually behaves."
 */
export interface Payment {
  id: string;
  loanEntryId: string;
  amount: Cents;
  paidAt: IsoDateString;
  note?: string;
  createdAt: IsoDateString;
}

/**
 * Status shown on a LoanStatusBadge.
 *
 * PENDING_SYNC is deliberately ABSENT in this phase — there is no sync
 * layer yet, and inventing a status the system cannot actually produce
 * would be a lie in the UI. It will be added by the platform-wide
 * Offline Engine later. Every consumer of this type must therefore have
 * a safe default branch in its switch, so adding that fourth member is a
 * colour-mapping change rather than an edit across several files.
 */
export type LoanStatus = "OUTSTANDING" | "PAID" | "OVERDUE";

/**
 * A LoanEntry joined with its payments and everything derived from them.
 * This is what screens actually render — they never compute anything
 * themselves (feature spec: "Screens orchestrate. They do not
 * calculate.").
 */
export interface LoanEntryView {
  entry: LoanEntry;
  payments: Payment[];
  /** Derived from payments, NEVER read from a stored column — see
   *  balanceCalculator for why. */
  outstandingAmount: Cents;
  amountPaid: Cents;
  status: LoanStatus;
  /** Whole days since saleDate. */
  ageInDays: number;
  /** Days past the overdue threshold; 0 when not overdue. */
  daysOverdue: number;
}

/** A customer plus the totals across all of their entries. */
export interface CustomerView {
  customer: Customer;
  entries: LoanEntryView[];
  totalOutstanding: Cents;
  totalOriginal: Cents;
  /** Entries not yet settled. */
  openEntryCount: number;
  hasOverdue: boolean;
  lastPaymentAt?: IsoDateString;
}

/** The Loan Book dashboard summary — the "what do I need to do right
 *  now" numbers (Doc 02 §1.3, §1.6). */
export interface LoanBookSummary {
  totalOutstanding: Cents;
  customersOwingCount: number;
  overdueCount: number;
  overdueAmount: Cents;
  /** Total collected in the trailing 30 days — the one genuinely
   *  encouraging number on the screen. */
  collectedLast30Days: Cents;
}

/** Filters applied to the Loan Book list. */
export interface LoanFilters {
  status?: LoanStatus;
  customerId?: string;
  /** Free-text match against customer name and phone. */
  searchTerm?: string;
  sortBy?: LoanSortOption;
}

export type LoanSortOption =
  | "NEWEST"
  | "OLDEST"
  | "HIGHEST_AMOUNT"
  | "LOWEST_AMOUNT"
  | "MOST_OVERDUE";

// ---------------------------------------------------------------------------
// Behavioural insights — FACTS ONLY, never risk labels
// ---------------------------------------------------------------------------

/**
 * Observable, factual statements about a customer's payment behaviour —
 * "usually pays within 8 days", "settled 8 of the last 9 purchases".
 *
 * DELIBERATE CONSTRAINT: the UI must NEVER render a risk grade
 * ("High/Medium/Low Risk") next to a named person. These customers never
 * signed up for anything, and a visible risk label on a private
 * individual is de-facto credit scoring of a third party — which Doc 04
 * §6 warns against ("not credit scores and must never be presented as
 * such") and which is very hard to walk back once shipped.
 *
 * riskIndicator.ts still COMPUTES a score, because TruePoint will
 * eventually consume that behavioural signal (Doc 07). It simply never
 * reaches the shop owner's screen. That separation is the whole point of
 * this type existing.
 */
export interface BehaviouralInsight {
  kind: InsightKind;
  /** Plain-language, jargon-free (Doc 02 §14): "Usually pays within 8 days". */
  statement: string;
  /** Whether this reads as encouraging, neutral, or worth attention.
   *  Drives tone/colour only — never a judgement label on the person. */
  tone: "POSITIVE" | "NEUTRAL" | "ATTENTION";
}

export type InsightKind =
  | "LAST_PAYMENT"
  | "AVERAGE_REPAYMENT_DAYS"
  | "SETTLEMENT_CONSISTENCY"
  | "OUTSTANDING_TREND"
  | "PURCHASE_FREQUENCY";

/**
 * Internal-only behavioural signal. Computed, stored, and eventually
 * shipped to TruePoint — but NEVER rendered. Kept as a distinct type
 * from BehaviouralInsight precisely so that "what we compute" and "what
 * we show" cannot be confused by a future reader.
 */
export interface InternalBehaviouralSignal {
  customerId: string;
  /** 0–100. Higher = more reliably settles. Not a credit score. */
  repaymentReliability: number;
  /** Predicted days until settlement, or null when there's too little
   *  history to say anything honest. */
  predictedDaysToSettle: number | null;
  /** How much history this is based on — a prediction from 2 payments
   *  should not be treated like one from 50. */
  sampleSize: number;
  calculatedAt: IsoDateString;
}

// ---------------------------------------------------------------------------
// Write payloads — shaped as the eventual Flask request bodies
// ---------------------------------------------------------------------------

export interface RecordCreditSaleInput {
  /** Existing customer, or omit and supply newCustomerName to create
   *  one inline — adding a customer must never be a separate screen the
   *  shop owner has to visit first. */
  customerId?: string;
  newCustomerName?: string;
  newCustomerPhone?: string;
  amount: Cents;
  saleDate?: IsoDateString;
  description?: string;
}

export interface RecordPaymentInput {
  loanEntryId: string;
  amount: Cents;
  paidAt?: IsoDateString;
  note?: string;
}

// ---------------------------------------------------------------------------
// Loan Book History — an append-only event log
// ---------------------------------------------------------------------------

/**
 * Every meaningful action the Loan Book can take, recorded once and
 * never modified afterward.
 *
 * WHY THIS SHAPE: it deliberately mirrors the platform Audit system
 * already built for Auth (src/domains/security/models/audit_event.py) —
 * same "one append-only event log" pattern, showing up in a second
 * domain because the underlying need ("what happened, when, to whom")
 * is the same need, not a coincidence. Kept Loan-Book-scoped for now
 * rather than prematurely merged into the shared Audit system, matching
 * the same "don't generalize before a second real feature needs it"
 * discipline already applied elsewhere in this project — a natural
 * candidate to fold into shared platform infrastructure once that
 * decision is made deliberately, not accidentally.
 */
export type LoanHistoryEventType =
  | "SALE_CREATED"
  | "PAYMENT_RECORDED"
  | "PAYMENT_REMOVED"
  | "ENTRY_DELETED"
  | "ENTRY_RESTORED"
  | "CUSTOMER_CREATED"
  | "CUSTOMER_DELETED"
  | "CUSTOMER_RESTORED"
  | "RECEIPT_VIEWED"
  | "RECEIPT_SHARED";

export interface LoanHistoryEvent {
  id: string;
  customerId: string;
  /** Absent for customer-level events (e.g. CUSTOMER_DELETED applies to
   *  the whole account, not one purchase). */
  loanEntryId?: string;
  eventType: LoanHistoryEventType;
  /** Relevant for SALE_CREATED / PAYMENT_RECORDED / PAYMENT_REMOVED. */
  amount?: Cents;
  description?: string;
  /** Deletion/removal reason, when applicable. */
  reason?: string;
  /** Who performed it. Optional today — Phase 1 has exactly one actor
   *  (the business owner using the app) — becomes meaningful once
   *  supplier_staff-style multi-user accounts exist (Doc 04 §4.3), at
   *  which point this answers "who modified it" without any shape
   *  change here. */
  performedBy?: string;
  occurredAt: IsoDateString;
}

export interface LoanHistoryFilters {
  customerId?: string;
  eventType?: LoanHistoryEventType;
}


/**
 * A deleted customer's Trash summary — deliberately NOT a list of their
 * individual entries. While a customer is in Trash, every one of their
 * purchases (cascade-deleted alongside them, or independently deleted
 * earlier and still gone) is already represented by this ONE row and
 * its counts.
 *
 * Shared by both mockLoanBookApi.ts and httpLoanBookApi.ts so neither
 * implementation depends on the other's internals.
 */
export interface DeletedCustomerSummary {
  customer: Customer;
  /** Purchases still unpaid at the time of deletion. */
  openEntryCount: number;
  totalEntryCount: number;
  totalOutstanding: Cents;
}

/** A deleted entry that earned its OWN Trash row — its customer is
 *  still active, so this was deleted independently, not as part of a
 *  customer-level cascade. Carries the customer's name for reference,
 *  since the row has no customer context otherwise. */
export interface DeletedEntrySummary {
  view: LoanEntryView;
  customerName: string;
}
