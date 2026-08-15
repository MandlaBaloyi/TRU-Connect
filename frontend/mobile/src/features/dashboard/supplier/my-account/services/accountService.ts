/**
 * Supplier My Account service — THE SINGLE INTEGRATION BOUNDARY for
 * everything this feature owns that isn't real yet. Same discipline
 * as business/my-account/services/accountService.ts: mock-backed,
 * in-memory, resets on app restart — replace the function body, not
 * the signature, when the real backend exists.
 *
 * Smaller surface than the business version on purpose — see
 * types.ts's header for why payment methods and business-details
 * editing aren't here at all, not even as stubs.
 */
import type {
  ConnectCode,
  DeactivationRequestStatus,
  DeleteAccountInput,
  DeletionRequestStatus,
  DisplayNameInput,
} from "../types";

const latency = () => new Promise<void>((resolve) => setTimeout(resolve, 300));

// --- Contact details --------------------------------------------------
// PHONE/EMAIL THEMSELVES ARE REAL — from AuthUser via useCurrentUser
// (GET /auth/me). No PATCH exists yet, so this simulates one — same
// session-persistent mock discipline as business/my-account's own
// updateContactField: the caller writes the result into the SAME
// React Query cache key useCurrentUser reads (see
// hooks/useContactDetails.ts), so the UI never shows a value that
// reverts on the next real-looking fetch.

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

// --- Business name (read-only subtitle) -----------------------------------
// Mocked, not real, unlike business/my-account's equivalent peek at
// BusinessProfile (which reads a REAL endpoint). No GET
// /supplier-discovery/my-profile exists yet — see types.ts's own
// future-contract note. Once it does, this becomes a real read the
// same way business's useAccountProfile already works, not a
// rewrite.

let mockBusinessName: string | null = "Your Business";

export async function getMyBusinessName(): Promise<string | null> {
  await latency();
  return mockBusinessName;
}

export async function updateMyBusinessName(value: string): Promise<string> {
  await latency();
  const trimmed = value.trim();
  if (trimmed.length === 0) {
    throw new Error("Enter your business name.");
  }
  mockBusinessName = trimmed;
  return mockBusinessName;
}

// --- Bio ------------------------------------------------------------------
// In-memory only, same reasoning as the business side's own bio mock:
// this is account data the future backend will own, so pretending a
// local save is durable would misrepresent that. Unlike Business's
// bio (a private blurb), THIS bio is SupplierProfile.description —
// already real, already shown to businesses in search results and
// profile previews today. Editing it here is editing something live,
// once the backend piece lands — worth remembering when writing UI
// copy for this screen.

let bioState: string | null = null;

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

// --- Account lifecycle requests ------------------------------------------
// Same non-negotiable rule as business/my-account/services/accountService.ts:
// these functions NEVER touch real accountStatus. accountStatus is
// read-only, straight from useCurrentUser(). This only simulates
// SUBMITTING a request.

let deactivationRequestState: DeactivationRequestStatus = "NONE";
let deletionRequestState: DeletionRequestStatus = "NONE";

export async function getDeactivationRequestStatus(): Promise<DeactivationRequestStatus> {
  await latency();
  return deactivationRequestState;
}

export async function requestDeactivation(): Promise<DeactivationRequestStatus> {
  await latency();
  deactivationRequestState = "SUBMITTED";
  return deactivationRequestState;
}

export async function getDeletionRequestStatus(): Promise<DeletionRequestStatus> {
  await latency();
  return deletionRequestState;
}

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
// Mirrors business/my-account/services/accountService.ts's own Connect
// Code section exactly — same reasoning, same mock discipline. See
// this feature's types.ts for the one real difference (direction of
// scanning).

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
