/**
 * localReminderService — reminders for the BUSINESS OWNER ONLY.
 *
 * ============================================================
 *  THIS MUST NEVER CONTACT A CUSTOMER.
 * ============================================================
 *
 * Doc 06 §16: "Loan Book reminders are business-local and never sent to
 * the customer by TRUConnect. The platform does not contact a business's
 * customers on its behalf."
 *
 * Doc 06 §17: "A business's Loan Book is private to that business. It is
 * never exposed to suppliers, other businesses, or (in TRUConnect) any
 * third party."
 *
 * The file is named `localReminderService` rather than `reminderService`
 * precisely so this constraint is impossible to misread. A generic name
 * invites someone to add "and also SMS the customer" as an obvious
 * improvement — which would mean TRU Connect messaging private
 * individuals about their debts, on a business's behalf, without their
 * consent. That is a POPIA problem and a trust problem, not a feature.
 *
 * Permitted: local device notifications to the phone running the app.
 * Forbidden: SMS, WhatsApp, email, or push to a customer.
 *
 * PHASE 1 STATUS: this module computes WHAT should be reminded about and
 * when. It deliberately does NOT schedule anything yet — scheduling needs
 * expo-notifications, which is not in the approved dependency list for
 * this phase (docs/10_Expo_SDK54_Dependency_Reference.txt). The pure
 * logic is written and testable now; wiring it to the OS notification
 * scheduler is a later, deliberate step.
 */

import type { CustomerView, LoanEntryView } from "../types";
import { formatCents } from "./loanMapper";

export interface OwnerReminder {
  id: string;
  /** Shown to the BUSINESS OWNER on their own device. Never sent to
   *  anyone else. */
  title: string;
  body: string;
  /** Which screen to open when tapped. */
  entityType: "LOAN_ENTRY" | "CUSTOMER";
  entityId: string;
  priority: "HIGH" | "NORMAL";
}

/**
 * Reminders worth surfacing today.
 *
 * Deliberately conservative: a reminder for every unpaid entry would be
 * noise, and noisy notifications get switched off entirely — after which
 * the useful ones never arrive either.
 */
export function buildOwnerReminders(
  entries: LoanEntryView[],
  customers: CustomerView[]
): OwnerReminder[] {
  const reminders: OwnerReminder[] = [];
  const nameById = new Map(customers.map((view) => [view.customer.id, view.customer.name]));

  // Newly overdue: crossed the threshold in the last day. Reminding once
  // at the moment it becomes overdue is useful; reminding every day
  // afterwards is nagging.
  entries
    .filter((view) => view.status === "OVERDUE" && view.daysOverdue >= 1 && view.daysOverdue <= 1)
    .forEach((view) => {
      const name = nameById.get(view.entry.customerId) ?? "A customer";
      reminders.push({
        id: `overdue-${view.entry.id}`,
        title: "Payment now overdue",
        body: `${name} still owes ${formatCents(view.outstandingAmount)}.`,
        entityType: "LOAN_ENTRY",
        entityId: view.entry.id,
        priority: "HIGH",
      });
    });

  // A customer whose total has grown past a point worth noticing.
  customers
    .filter((view) => view.hasOverdue && view.openEntryCount >= 3)
    .forEach((view) => {
      reminders.push({
        id: `accumulating-${view.customer.id}`,
        title: "Several unpaid purchases",
        body: `${view.customer.name} has ${view.openEntryCount} unpaid purchases totalling ${formatCents(view.totalOutstanding)}.`,
        entityType: "CUSTOMER",
        entityId: view.customer.id,
        priority: "NORMAL",
      });
    });

  return reminders;
}

/**
 * Scheduling is not implemented in Phase 1 — see the module docstring.
 * Present as an explicit, documented no-op rather than an absent
 * function, so a caller added later fails loudly at the review stage
 * rather than silently doing nothing in production.
 */
export async function scheduleOwnerReminder(_reminder: OwnerReminder): Promise<void> {
  throw new Error(
    "localReminderService.scheduleOwnerReminder is not implemented in Phase 1. " +
      "It requires expo-notifications, which is not in the approved dependency " +
      "list for this phase. Reminders must be LOCAL to the business owner's " +
      "device only — never SMS, WhatsApp, email, or push to a customer (Doc 06 §16)."
  );
}
