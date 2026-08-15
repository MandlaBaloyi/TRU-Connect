/**
 * My Account service — THE SINGLE INTEGRATION BOUNDARY for everything
 * this feature owns that ISN'T real yet (payment methods, bio,
 * deactivation/deletion requests). Same discipline as
 * security/services/securityService.ts:
 *
 * Every function below is backed by in-memory mock state. NO fake HTTP
 * calls, NO invented endpoints — when the backend exists, replace each
 * function body with a real apiGet/apiPost/apiPatch/apiDelete call. The
 * signatures are the contract (see types.ts's documented future
 * endpoints); hooks/screens above this file need no changes at all.
 *
 * Mock state lives in module scope: it survives navigation within a
 * session (add a payment method, go back, it's still there) but resets
 * on app restart. That's deliberate — persisting this locally would
 * misrepresent what's actually enforced server-side. NOTHING here is
 * written to AsyncStorage or secureStorage.
 *
 * ============================================================
 * account status / deactivation / deletion — read before touching
 * ============================================================
 * requestDeactivation() and requestAccountDeletion() below NEVER
 * change accountStatus. There is no code path in this file, or
 * anywhere else in this feature, that can flip a real account's
 * status — accountStatus is read-only, straight from AuthUser (see
 * auth/hooks/useCurrentUser.ts). These two functions only simulate
 * SUBMITTING a request and return a SUBMITTED marker; the screens that
 * call them are required to say plainly that nothing has actually
 * changed yet (file.txt §21: never silently save security-sensitive
 * state locally and pretend it's authoritative).
 */
import type {
  AddPaymentMethodInput,
  ConnectCode,
  DeactivationRequestStatus,
  DeleteAccountInput,
  DeletionRequestStatus,
  DisplayNameInput,
  PaymentMethod,
} from "../types";

const latency = () => new Promise<void>((resolve) => setTimeout(resolve, 300));

function generateId(prefix: string): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

// --- Mock state (module scope; see docstring) --------------------------

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

/** In-memory only, on purpose — see this file's own docstring on why
 *  mock security/account state is never persisted to AsyncStorage. A
 *  short bio genuinely isn't sensitive, but it IS account data the
 *  future backend will own; pretending a local save is durable would
 *  misrepresent that, the same way a fake-persisted 2FA toggle would. */
let bioState: string | null = null;

let deactivationRequestState: DeactivationRequestStatus = "NONE";
let deletionRequestState: DeletionRequestStatus = "NONE";

// --- Contact details ------------------------------------------------------
//
// PHONE/EMAIL THEMSELVES ARE REAL — they come from AuthUser via
// useCurrentUser (GET /auth/me). There is no PATCH /account/profile
// yet, so this simulates one: same session-persistent mock discipline
// Security already uses for password/2FA (mock state that genuinely
// "sticks" for the session, clearly commented as mock, never written
// to storage). The caller (hooks/useContactDetails.ts) is responsible
// for writing the result into the SAME React Query cache key
// useCurrentUser reads, so the UI never shows a value that reverts —
// see that hook for why this matters more here than it does for, say,
// bio, which has no real counterpart to contradict.

export type ContactField = "phone" | "email";

export async function updateContactField(field: ContactField, value: string): Promise<string> {
  await latency();
  const trimmed = value.trim();
  if (field === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
    throw new Error("Enter a valid email address.");
  }
  if (field === "phone" && trimmed.replace(/\D/g, "").length < 9) {
    throw new Error("Enter a valid phone number.");
  }
  return trimmed;
}

export async function updateDisplayName(input: DisplayNameInput): Promise<DisplayNameInput> {
  await latency();
  const firstName = input.firstName.trim();
  const lastName = input.lastName.trim();
  if (firstName.length === 0) {
    throw new Error("Enter your first name.");
  }
  return { firstName, lastName };
}

// --- Bio ----------------------------------------------------------------

export async function getBio(): Promise<string | null> {
  await latency();
  return bioState;
}

export async function updateBio(bio: string): Promise<string> {
  await latency();
  const trimmed = bio.trim();
  bioState = trimmed.length > 0 ? trimmed : null;
  return bioState as string;
}

// --- Payment methods ------------------------------------------------------

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
    // yet. See file.txt §21: never present unverified state as active.
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
    throw new Error("Cash can't be removed — it's the default offline payment method.");
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

// --- Account lifecycle requests ------------------------------------------

export async function getDeactivationRequestStatus(): Promise<DeactivationRequestStatus> {
  await latency();
  return deactivationRequestState;
}

/** Simulates SUBMITTING a deactivation request only — see this file's
 *  top docstring. Never touches real accountStatus. */
export async function requestDeactivation(): Promise<DeactivationRequestStatus> {
  await latency();
  deactivationRequestState = "SUBMITTED";
  return deactivationRequestState;
}

export async function getDeletionRequestStatus(): Promise<DeletionRequestStatus> {
  await latency();
  return deletionRequestState;
}

/** Simulates SUBMITTING a deletion request, including a mock
 *  re-authentication check — see this file's top docstring. Never
 *  deletes anything, never touches real accountStatus. */
export async function requestAccountDeletion(input: DeleteAccountInput): Promise<DeletionRequestStatus> {
  await latency();
  // NEVER log `input` — it carries a plaintext password.
  if (!input.currentPassword) {
    throw new Error("Enter your password to confirm.");
  }
  deletionRequestState = "SUBMITTED";
  return deletionRequestState;
}

// --- Connect Code (QR) ----------------------------------------------------
// See types.ts's own extensive note on this concept. MOCK, session-
// scoped: the token below is a random-looking string generated
// client-side purely so the QR rendering/regenerate flow is real and
// reviewable now — it is NOT a real opaque backend-issued token (there
// is no backend lookup for it to mean anything against yet), and it
// deliberately does NOT encode user_id/role, matching what the real
// one won't either.

function generateMockToken(): string {
  const bytes = Array.from({ length: 16 }, () => Math.floor(Math.random() * 256));
  return bytes.map((b) => b.toString(16).padStart(2, "0")).join("");
}

let connectCodeState: ConnectCode = { token: generateMockToken(), createdAt: new Date().toISOString() };

export async function getConnectCode(): Promise<ConnectCode> {
  await latency(150);
  return connectCodeState;
}

export async function regenerateConnectCode(): Promise<ConnectCode> {
  await latency(300);
  connectCodeState = { token: generateMockToken(), createdAt: new Date().toISOString() };
  return connectCodeState;
}
