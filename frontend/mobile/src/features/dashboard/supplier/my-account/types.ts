/**
 * Supplier My Account — personal account identity, contact, and
 * account lifecycle. The direct supplier-side counterpart to
 * business/my-account/types.ts, with two deliberate differences from
 * that template — both explicit product decisions, not oversights:
 *
 * 1. NO payment methods here. Business's version made sense because
 *    it's about PAYING a supplier — a real, already-modelled
 *    direction (Cash/EFT). A supplier's equivalent would be "how do I
 *    get paid", and nothing about receiving payment exists anywhere
 *    yet; it depends on Stock Ordering, which isn't built. Adding
 *    even a "Coming soon" stub here would promise a shape that hasn't
 *    been designed yet — better to add it once there's something real
 *    to point at.
 *
 * 2. NO business-details editing (business name / category /
 *    location) here. Those fields live on SupplierProfile, but
 *    editing them is deliberately OUT of this feature's scope — they
 *    get their own dedicated feature later, specifically because
 *    they'll double as verification-relevant data (file.txt's later
 *    "verification wall" phase). This screen only ever READS the
 *    business name, as a subtitle, the exact same read-only-peek
 *    pattern business/my-account's own useAccountProfile.ts already
 *    established for the identical situation on the business side.
 *
 * ============================================================
 * WHAT IS REAL VS MOCK RIGHT NOW
 * ============================================================
 * GENUINELY REAL, backend-authoritative today:
 *   - accountStatus, verificationStatus, firstName, lastName, email,
 *     phoneNumber — from AuthUser via the existing GET /auth/me (see
 *     auth/hooks/useCurrentUser.ts, already real, already shared).
 *   - businessName — read-only, from SupplierProfile via the existing
 *     GET /supplier-discovery/customer-requests-adjacent read path
 *     (see hooks/useAccountProfile.ts for exactly which query this
 *     reuses).
 * MOCK-BACKED, real contract, resets on app restart
 * (services/accountService.ts) — same discipline as
 * business/my-account/services/accountService.ts:
 *   - bio, deactivation/deletion REQUESTS (never actual enforcement).
 * NOT BUILT ANYWHERE, frontend contract only (see the bottom of this
 * file for the documented future endpoints):
 *   - PATCH /account/profile equivalent for bio/contact — this whole
 *     feature is frontend-only this round, by explicit instruction:
 *     build the UI against a real contract shape, review it, THEN
 *     build the backend — same phased process Find Supplier itself
 *     started with.
 */

import type { AccountStatus } from "@/features/auth/types";

export type { AccountStatus };

// ---------------------------------------------------------------------------
// Trust Verification — DELIBERATELY SEPARATE from AuthUser.verificationStatus.
// Mirrors business/my-account/types.ts's own extensive note exactly — this
// matters identically on both sides: a supplier's email being confirmed
// via OTP tells a business nothing about whether that supplier is a real,
// checked business. Always "NOT_VERIFIED" right now, hardcoded, not
// derived from anything — see hooks/useAccountProfile.ts's own note.
// ---------------------------------------------------------------------------

export type TrustVerificationStatus = "NOT_VERIFIED" | "VERIFIED";

export const BIO_MAX_LENGTH = 140;

export type DeletionRequestStatus = "NONE" | "SUBMITTED";
export type DeactivationRequestStatus = "NONE" | "SUBMITTED";

export interface DeleteAccountInput {
  currentPassword: string;
  reason?: string;
}

/** Everything the landing screen needs, assembled once — mirrors
 *  business/my-account's AccountProfileSummary exactly, with
 *  businessName sourced from SupplierProfile instead of
 *  BusinessProfile. */
export interface AccountProfileSummary {
  firstName: string | null;
  lastName: string | null;
  email: string;
  phoneNumber: string | null;
  /** Read-only, from SupplierProfile — see this file's header. */
  businessName: string | null;
  /** Also from SupplierProfile — genuinely SupplierProfile.description,
   *  see accountService.ts's own note on why this and businessName
   *  are the same real profile, not two separate reads. */
  bio: string | null;
  verification: TrustVerificationStatus;
  accountStatus: AccountStatus | null;
}

// ---------------------------------------------------------------------------
// Connect Code (QR) — direct counterpart to business/my-account's own
// ConnectCode. Same opaque-by-design trust model, same reasoning for
// why it's a durable/rotatable concept rather than a one-time
// invitation ticket — see business/my-account/types.ts's own extensive
// note, not repeated here.
//
// The one real difference worth naming: a SUPPLIER's Connect Code is
// what a BUSINESS scans (the reverse direction of Find Supplier's own
// search), and the future backend's role-mismatch rejection applies
// here identically — a supplier scanning another supplier's code must
// be rejected server-side, with a clear reason, the same as the
// business side.
// ---------------------------------------------------------------------------

export interface ConnectCode {
  token: string;
  createdAt: string;
}

/** Lightweight display name — edits AuthUser's own firstName/lastName.
 *  NOT business identity, same distinction business/my-account draws. */
export interface DisplayNameInput {
  firstName: string;
  lastName: string;
}

// ---------------------------------------------------------------------------
// Payment methods — the RECEIVING side, the reverse direction of
// business/my-account's own PaymentMethod (which is about PAYING a
// supplier). A supplier's equivalent question is "how do I get paid
// by a business", which is the direct mirror of that already-real
// Cash/EFT model, not a new concept invented from nothing — same
// two methods, same reasoning for why EFT leaves a real digital trail
// and cash doesn't (see business/my-account/types.ts's own note on
// PaymentMethodType for the fuller explanation, not repeated here).
//
// CASH LIMIT: explicitly NOT implemented here, on purpose — a
// threshold above which cash alone isn't enough evidence of a real
// payment is a genuine future requirement (same note business's own
// PaymentMethodType makes), but it depends on Stock Ordering's real
// transaction amounts to check against, which doesn't exist yet.
// ---------------------------------------------------------------------------

export type PaymentMethodType = "CASH" | "EFT";
export type PaymentMethodStatus = "ACTIVE" | "PENDING_VERIFICATION" | "REMOVED";

export interface PaymentMethod {
  id: string;
  type: PaymentMethodType;
  /** Bank name for EFT (e.g. "FNB", "Capitec") — null for CASH. */
  provider: string | null;
  displayLabel: string;
  maskedReference: string | null;
  status: PaymentMethodStatus;
  isDefault: boolean;
}

/** EFT-only, same reasoning as business's own AddPaymentMethodInput —
 *  CASH is seeded automatically and always present. */
export interface AddPaymentMethodInput {
  type: "EFT";
  provider: string;
  /** Already-masked by the caller — never a raw account number. */
  maskedReference: string;
  displayLabel: string;
}

// ---------------------------------------------------------------------------
// Subscription & Billing — file.txt Phase-agnostic, this is TRU
// Connect's own platform-usage model, not a stock-order/payment
// concept. Three tiers this round (Free / Pro / Max) — Enterprise is
// explicitly a later addition per the product roadmap, not scoped yet.
//
// PROVISIONAL, NOT A COMMITMENT: the specific limits/features listed
// per tier below are placeholders reflecting what's been discussed so
// far (order volume, catalogue size, search priority, web portal
// access for Pro/Max) — genuinely not finalised. Marked clearly in
// the UI copy itself, not just here, so nobody mistakes a placeholder
// number for a real price or limit.
//
// EVERYONE IS "FREE" RIGHT NOW, HARDCODED — there is no billing
// infrastructure anywhere in this codebase (Card payments on the
// business side are an honest "Coming soon" stub for the identical
// reason). Upgrading doesn't charge anything; it shows the same
// honest "not connected yet" treatment as everywhere else unbuilt
// backend shows up in this app.
// ---------------------------------------------------------------------------

export type SubscriptionTier = "FREE" | "PRO" | "MAX";

export interface SubscriptionTierInfo {
  tier: SubscriptionTier;
  name: string;
  /** Display only, provisional — see this section's own note. */
  priceLabel: string;
  features: string[];
  hasWebPortalAccess: boolean;
}

export interface SupplierSubscription {
  tier: SubscriptionTier;
  /** null for FREE — there's nothing to bill. */
  nextBillingDate: string | null;
}

// ---------------------------------------------------------------------------
// FUTURE BACKEND CONTRACT — none of this exists yet. Frontend-only this
// round, by explicit instruction: build against this contract, review,
// then build the backend.
// ---------------------------------------------------------------------------

/**
 * GET    /auth/me                          — ALREADY REAL, reused as-is
 * GET    /supplier-discovery/my-profile     — ALREADY REAL data source
 *                                             (SupplierProfile), but no
 *                                             route reads it back for
 *                                             the OWNING supplier yet —
 *                                             only search/customer-
 *                                             requests read it today.
 * PATCH  /supplier-discovery/my-profile     — bio + firstName/lastName
 *                                             this round (businessName/
 *                                             category/location
 *                                             deliberately excluded —
 *                                             see this file's header).
 * POST   /account/deactivate
 * POST   /account/delete                    — requires re-auth
 * GET    /account/connect-code
 * POST   /account/connect-code/regenerate
 * POST   /connect-codes/{token}/resolve     — same role-mismatch
 *                                             rejection as the business
 *                                             side's own contract note.
 * GET    /account/payment-methods
 * POST   /account/payment-methods
 * DELETE /account/payment-methods/{id}
 * PATCH  /account/payment-methods/{id}/default
 * GET    /account/subscription
 * POST   /account/subscription/upgrade      — requires real billing
 *                                             infrastructure first;
 *                                             see this file's own
 *                                             Subscription note.
 */
