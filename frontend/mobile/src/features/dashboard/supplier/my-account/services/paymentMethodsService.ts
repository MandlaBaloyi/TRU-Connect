/**
 * Payment Methods service — the RECEIVING side, supplier's own
 * integration boundary. Mirrors business/my-account/services/
 * accountService.ts's own payment-methods section exactly (same
 * mock discipline, same CASH-seed-plus-EFT-add pattern) — see
 * types.ts's own note on why this is the direct mirror of that
 * already-real model, not a new concept.
 */
import type { AddPaymentMethodInput, PaymentMethod } from "../types";

const latency = () => new Promise<void>((resolve) => setTimeout(resolve, 300));

function generateId(prefix: string): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

let paymentMethods: PaymentMethod[] = [
  {
    id: "pm_cash",
    type: "CASH",
    provider: null,
    displayLabel: "Cash",
    maskedReference: null,
    status: "ACTIVE",
    isDefault: true,
  },
];

export async function getPaymentMethods(): Promise<PaymentMethod[]> {
  await latency();
  return paymentMethods;
}

/** EFT-only — see AddPaymentMethodInput's own doc comment on why. */
export async function addPaymentMethod(input: AddPaymentMethodInput): Promise<PaymentMethod> {
  await latency();
  const method: PaymentMethod = {
    id: generateId("pm"),
    type: "EFT",
    provider: input.provider,
    displayLabel: input.displayLabel,
    maskedReference: input.maskedReference,
    // New EFT methods start pending — nothing in this mock (or a real
    // backend, on day one) has actually verified the bank reference
    // yet. Never present unverified state as active.
    status: "PENDING_VERIFICATION",
    isDefault: paymentMethods.length === 0,
  };
  paymentMethods = [...paymentMethods, method];
  return method;
}

export async function removePaymentMethod(id: string): Promise<void> {
  await latency();
  const target = paymentMethods.find((m) => m.id === id);
  if (target?.type === "CASH") {
    throw new Error("Cash can't be removed — it's the default way to receive payment.");
  }
  const wasDefault = target?.isDefault ?? false;
  paymentMethods = paymentMethods.filter((m) => m.id !== id);
  if (wasDefault && paymentMethods.length > 0) {
    paymentMethods = paymentMethods.map((m, i) => ({ ...m, isDefault: i === 0 }));
  }
}

export async function setDefaultPaymentMethod(id: string): Promise<void> {
  await latency();
  paymentMethods = paymentMethods.map((m) => ({ ...m, isDefault: m.id === id }));
}
