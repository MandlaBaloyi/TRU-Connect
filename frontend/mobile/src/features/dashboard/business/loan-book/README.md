# Loan Book

Replaces the handwritten "Pay Later" notebook used by informal
businesses. Records money a **customer owes this business** from a credit
sale.

**Scope boundary (Doc 04 §3.5):** record-keeping only. TRUConnect does
not lend, does not hold funds, does not collect, and charges no interest.
Nothing in this feature may grow into a lending product.

---

## Phase 1 — what this is

Frontend-first. The complete UX, running on an in-memory repository.

```
UI  ->  Hooks  ->  loanBookApi.ts  ->  LoanRepository  ->  MockDataRepository
```

The UX is being validated before any backend or persistence is written,
because **user experience is harder to change than a data source**. Screen
layout, tap counts, and whether a screen should exist at all are cheapest
to get wrong while the data is fake.

---

## Deliberately absent — do not add these here

This feature contains **no offline implementation**, and that is a
decision rather than an omission:

- ❌ `offlineStorage.ts`
- ❌ `syncService.ts`
- ❌ `useOfflineLoanBook.ts`
- ❌ `offlineSyncResolver.ts`
- ❌ `SyncIndicator.tsx`
- ❌ SQLite, sync queues, conflict resolution, NetInfo

**Why not even empty stubs:** an empty `syncService.ts` sitting in this
folder is a file someone eventually fills in *for the Loan Book
specifically*. Do that across Orders, Inventory, Nearby Suppliers, and
Business Profile as well, and TRU Connect ends up with five
feature-specific offline implementations to reconcile instead of one
engine.

Offline support belongs to **platform infrastructure**, and will be built
once, for every feature:

```
Business Profile   Orders   Loan Book   Inventory   Nearby Suppliers
                          │
                Shared Offline Repository
                          │
                       SQLite
                          │
                     Sync Queue
                          │
                        Flask
```

The following will be introduced later by that shared infrastructure —
not by this feature:

- `offlineRepository`
- `syncQueue`
- `conflictResolver`
- `syncService`
- `localStorageProvider`

`LoanStatus` will gain a `PENDING_SYNC` member at that point. Every
consumer already has a safe default branch, so adding it is a
colour-mapping change rather than an edit across several files.

---

## Swapping the data source

One line, in `api/loanBookApi.ts`:

```ts
const repository: LoanRepository = new MockDataRepository();
// later:
const repository: LoanRepository = new ApiRepository();
// later still:
const repository: LoanRepository = new OfflineRepository();
```

No hook, screen, or component changes. That is the whole point of the
`LoanRepository` interface.

---

## Rules encoded here

| Rule | Where | Source |
|---|---|---|
| Outstanding is **derived**, never read from a stored column | `algorithms/balanceCalculator.ts` | standard accounting practice |
| Overdue = outstanding after 30 days from `sale_date` (no due-date field) | `algorithms/agingCalculator.ts` | Doc 02 §1.2 (minimum typing) |
| Repayments may not be negative or exceed outstanding | `algorithms/paymentAllocation.ts` | Doc 06 §12.3 |
| Partial repayment fully supported | throughout | Doc 06 §12.3 |
| Money is **integer cents**, never floats | `types.ts` | Doc 04 §9.1 |
| Entries are soft-deleted | `loanBookApi.deleteLoanEntry` | Doc 06 §17 |
| IDs are client-generated UUIDs | `loanBookApi.generateId` | Doc 04 §5.1 |

The 30-day overdue threshold is a named constant
(`DEFAULT_OVERDUE_THRESHOLD_DAYS`) and every function accepts it as a
parameter, so making it a per-business setting (7/14/21/30/45/60) later
requires no changes to the algorithms.

---

## Behavioural insights — facts, never risk labels

`riskIndicator.ts` and `repaymentPredictor.ts` compute numeric
behavioural signals for eventual TruePoint consumption (Doc 07). **These
must never be rendered.**

The customers in this book are private individuals who never signed up
for TRU Connect — a shop's neighbours. A visible "High Risk" label next
to a named person is de-facto credit scoring of a third party, which
Doc 04 §6 warns against and which is very hard to walk back once
shipped.

What the shop owner sees instead are **verifiable facts**:

- "Last paid 4 days ago"
- "Usually pays within 8 days"
- "Settled 8 of 9 purchases"

Safe to render: `describeRepaymentBehaviour()`, `describePurchaseFrequency()`,
`describeOverdueFact()` (a fact about a *debt*, not a person).

Never render: `predictRepaymentBehaviour()`,
`computeRiskSignalForInternalUse()`, `computeInternalRiskComponents()`.

---

## Reminders are business-local only

`localReminderService.ts` is named that way deliberately. Doc 06 §16:

> Loan Book reminders are business-local and never sent to the customer
> by TRUConnect. The platform does not contact a business's customers on
> its behalf.

It schedules **local device notifications to the business owner**. It must
never send SMS, WhatsApp, email, or push notifications to a customer.

Doc 06 §17: a business's Loan Book is private to that business and is
never exposed to suppliers, other businesses, or any third party.

---

## Structure

```
loan-book/
├── algorithms/          pure: no UI, no API, no storage
│   ├── agingCalculator.ts
│   ├── balanceCalculator.ts
│   ├── paymentAllocation.ts
│   ├── repaymentPredictor.ts
│   └── riskIndicator.ts        (internal only — see above)
├── api/
│   ├── loanBookApi.ts          the ONLY data boundary
│   └── repository/
│       ├── LoanRepository.ts   the swap point
│       └── MockDataRepository.ts
├── components/
├── hooks/
├── screens/
├── services/
│   ├── loanFilters.ts
│   ├── loanMapper.ts
│   ├── loanValidation.ts
│   └── localReminderService.ts
├── types.ts
└── README.md
```

Screens orchestrate. They do not calculate, validate, or transform.
Screens call hooks; hooks call the API; the API composes services and
algorithms.
