/**
 * My Account — personal account identity, contact, payment methods,
 * file/upload architecture, and account lifecycle.
 *
 * FRONTEND-ONLY PHASE (file.txt this round). These types are the
 * CONTRACT the future backend will implement. Every type below is
 * shaped the way a real API would actually return it, so wiring the
 * backend later is a service-layer swap, not a UI rewrite — same
 * discipline as security/types.ts.
 *
 * ============================================================
 * DATA OWNERSHIP — read this before adding a field here
 * ============================================================
 * My Account owns PERSONAL account identity: your name, your contact
 * details, your bio as the account holder, your payment methods, your
 * account lifecycle. It does NOT own business identity — that's
 * business-profile's job (business name, category, trading details,
 * location). Where My Account's UI needs to *display* something
 * business-profile owns (the business name shown as a subtitle on the
 * profile header), it reads business-profile's own query — see
 * hooks/useAccountProfile.ts — rather than duplicating that field
 * here. This mirrors business-profile/types.ts's own explicit rule
 * that one feature owning a live copy of another feature's data is
 * not fine, but two features modelling similar concepts independently
 * is.
 *
 * ============================================================
 * WHAT IS REAL VS MOCK RIGHT NOW — read this before assuming either
 * ============================================================
 * GENUINELY REAL, backend-authoritative today:
 *   - accountStatus, verificationStatus, firstName, lastName, email,
 *     phoneNumber — all come straight from AuthUser via the existing,
 *     already-implemented GET /auth/me (see auth/hooks/useCurrentUser.ts).
 *     My Account does not re-model these; it reads them.
 * MOCK-BACKED, real contract, resets on app restart (services/accountService.ts,
 * services/fileRepository.ts — same discipline as securityService.ts,
 * "replace the function body, not the signature"):
 *   - bio, payment methods, profile image, deactivation/deletion
 *     REQUESTS (never actual enforcement). Proof-of-payment is NOT
 *     part of this feature — see the note above PaymentMethodType.
 * NOT BUILT ANYWHERE, frontend contract only (see the bottom of this
 * file for the documented future endpoints):
 *   - Actual account suspension/deactivation/deletion enforcement,
 *     actual file security scanning, actual payment-provider tokenisation.
 */

import type { AccountStatus } from "@/features/auth/types";

export type { AccountStatus };

// ---------------------------------------------------------------------------
// Trust Verification — DELIBERATELY SEPARATE from AuthUser.verificationStatus.
// That field only ever means "this person's email was confirmed via OTP"
// (see auth/services/otp_service.py) — real, but nowhere near sufficient
// to tell a business "this supplier is verified," or a supplier "this
// business is verified." TRU Connect's own real verification (identity +
// business details, eventually gated behind a paid subscription tier per
// the product roadmap) doesn't exist yet, and this type deliberately
// doesn't pretend otherwise by borrowing the email-confirmation field for
// it — a previous version of this screen did exactly that, and it was a
// real bug, not just a naming issue: it would have told businesses at
// scale that "verified" meant something it never actually checked.
//
// ALWAYS "NOT_VERIFIED" right now, hardcoded, not derived from anything —
// see hooks/useAccountProfile.ts's own note. The one thing this type is
// FOR is being the single place that changes once real verification
// logic exists — nothing that reads TrustVerificationStatus needs to
// change when that day comes, only what populates it.
// ---------------------------------------------------------------------------

export type TrustVerificationStatus = "NOT_VERIFIED" | "VERIFIED";

// ---------------------------------------------------------------------------
// File / upload architecture — provider-neutral (file.txt §3, §7, §9).
// Never coupled to S3/Firebase/Drive/Cloudinary by name anywhere in this
// feature. The backend decides where a file physically lives; the
// frontend only ever sees these states.
// ---------------------------------------------------------------------------

/** The full async upload lifecycle. Upload finishing is NOT the same as
 *  the file being approved — file.txt §9 is explicit that these must
 *  stay distinct states, never collapsed into one. */
export type UploadStatus =
  | "idle"
  | "selecting"
  | "selected"
  | "uploading"
  | "processing"
  | "approved"
  | "rejected"
  | "failed"
  | "cancelled";

/** Provider-neutral file kind. Deliberately NOT a MIME type string —
 *  see file.txt §24: never trust client MIME type as a security
 *  signal. This is a display/UI hint only. */
export type FileKind = "IMAGE" | "PDF" | "OTHER";

/** An uploaded (or in-flight) file, however it will eventually be
 *  stored. No bucket name, no provider, no raw storage path — those
 *  are backend concerns the frontend must never assume (file.txt §3, §10). */
export interface FileAsset {
  /** Opaque backend-issued id once uploaded. Absent while still local
   *  (selected but not yet uploaded). */
  id: string | null;
  /** Local device URI, present only before/while uploading — never
   *  sent anywhere once approved storage exists. */
  localUri: string | null;
  kind: FileKind;
  /** Original filename, for display only — NEVER trusted for
   *  validation (file.txt §24). */
  fileName: string;
  /** Bytes, client-reported — a UI hint only; the backend enforces
   *  the real size limit. */
  sizeBytes: number | null;
  status: UploadStatus;
  /** Set only on rejected/failed — always a SAFE, generic message.
   *  Never a scanner/parser detail (file.txt §7: no "ClamAV detected
   *  signature XYZ" — that belongs in backend audit logs only). */
  statusMessage: string | null;
  createdAt: string;
}

/** One upload's lifecycle, separate from the FileAsset it produces —
 *  lets the UI show "uploading 40%"-style progress without pretending
 *  that progress is the same thing as backend approval. */
export interface UploadSession {
  sessionId: string;
  asset: FileAsset;
  /** 0-100. Only meaningful while status is "uploading". */
  progressPercent: number;
}

/** What the profile-image flow specifically produces. Same shape as
 *  FileAsset — a distinct name only so screens/hooks read clearly
 *  ("this is specifically the avatar", not "some file somewhere"). */
export type ProfileImageAsset = FileAsset;

// NOTE: there is deliberately no PaymentProof type here anymore.
// Proof-of-payment belongs to a specific stock order (business orders
// stock from a supplier, chooses Cash or EFT for THAT order, and — for
// EFT — attaches proof against THAT order), which is the future Stock
// Order feature's domain, not My Account's. My Account only owns which
// payment methods exist and which one is default; it was previously
// modelled here before that ownership was clarified, and has been
// moved out accordingly (see PaymentMethod below and the future-
// contract note at the bottom of this file). The FileAsset/UploadStatus
// machinery above is still the right foundation to reuse for it when
// Stock Order is built — see fileRepository.ts's own note on why its
// document-picker path was removed for now rather than left dangling
// with no caller.

// ---------------------------------------------------------------------------
// Payment methods — file.txt §11, refined against how this actually
// gets used: a business orders stock from a supplier (the future Stock
// Order feature) and chooses, per order, which of ITS configured
// payment methods to pay with. My Account is where those methods are
// configured; Stock Order is where one gets picked per order.
//
//   Method  How money moves                    TruConnect's role today
//   Cash    Physical money -> supplier          Record + confirmation
//   EFT     Bank account -> bank account         Record + confirmation
//                                                 (+ proof, once Stock
//                                                 Order exists to attach
//                                                 it to — see note above)
//   Card    Payment provider -> supplier         Not built — shown as
//           (a payment gateway, later)           Coming soon below
//
// EFT matters specifically because it leaves a real digital banking
// trail, unlike cash — which is also why cash (not EFT) is the one
// that will eventually need a value limit: past a certain amount,
// cash alone isn't enough evidence of payment. That threshold depends
// on transaction amounts Stock Order will define, so it's deliberately
// NOT implemented here — noted for when that feature exists, not
// guessed at now.
//
// Never a raw card number, never a CVV, never a PIN, never stored
// anywhere in this app, mock or otherwise.
// ---------------------------------------------------------------------------

/** CASH and EFT are real, configurable methods today. CARD represents
 *  a future payment-gateway integration — it has no addable
 *  PaymentMethod of its own yet; it only exists as a Coming Soon row
 *  in the UI (see PaymentMethodsScreen), never a method a business can
 *  actually select. */
export type PaymentMethodType = "CASH" | "EFT";

export type PaymentMethodStatus = "ACTIVE" | "PENDING_VERIFICATION" | "REMOVED";

/** Deliberately resembles a tokenised-reference shape, never raw
 *  credentials (file.txt §11's own example). `maskedReference` is
 *  something like "•••• 4821" — display-safe by construction, never a
 *  field that COULD hold a full account/card number. */
export interface PaymentMethod {
  id: string;
  type: PaymentMethodType;
  /** The bank name for EFT (e.g. "FNB", "Capitec") — null for CASH,
   *  which has no provider. */
  provider: string | null;
  displayLabel: string;
  maskedReference: string | null;
  status: PaymentMethodStatus;
  isDefault: boolean;
}

/** Adding a method is EFT-only today — CASH is seeded automatically
 *  and always present (see accountService.ts), and CARD isn't
 *  addable until the future gateway integration exists. */
export interface AddPaymentMethodInput {
  type: "EFT";
  /** Bank name. */
  provider: string;
  /** Already-masked by the caller — this service never receives or
   *  handles a raw account number, mock or otherwise. */
  maskedReference: string;
  displayLabel: string;
}

// ---------------------------------------------------------------------------
// Account lifecycle — file.txt §4, §17, §21. accountStatus itself comes
// from the REAL AuthUser (see ownership note at the top of this file).
// These types cover the REQUEST/UI side only — submitting a deactivation
// or deletion request is not the same as it being enforced, and this
// feature never pretends otherwise.
// ---------------------------------------------------------------------------

export type DeletionRequestStatus = "NONE" | "SUBMITTED";
export type DeactivationRequestStatus = "NONE" | "SUBMITTED";

export interface AccountLifecycleState {
  /** Real, from AuthUser — see ownership note above. */
  accountStatus: AccountStatus | null;
  /** Backend-supplied reason for suspension. Null until a real
   *  suspension endpoint exists — never fabricated client-side. */
  suspensionReason: string | null;
  deactivationRequest: DeactivationRequestStatus;
  deletionRequest: DeletionRequestStatus;
}

export interface DeleteAccountInput {
  /** Re-authentication step — file.txt §4/§17: deletion should require
   *  re-auth where the future backend requires it. Verified against
   *  the mock only; a real implementation verifies server-side. */
  currentPassword: string;
  reason?: string;
}

// ---------------------------------------------------------------------------
// Bio — file.txt §4 "About" section. Deliberately tiny: a short,
// account-holder description, NOT business-profile's own structured
// `businessDetails.description`. Kept separate per this feature's data-
// ownership rule above; see business-profile/types.ts for the business-
// level field this is intentionally NOT reusing.
// ---------------------------------------------------------------------------

export const BIO_MAX_LENGTH = 140;

// ---------------------------------------------------------------------------
// Everything the My Account landing screen needs in derived form, so the
// screen composes real (AuthUser) + business-profile (read-only) + mock
// (accountService) data without three separate loading states racing —
// see hooks/useAccountProfile.ts, the only place this is assembled.
// ---------------------------------------------------------------------------

export interface AccountProfileSummary {
  firstName: string | null;
  lastName: string | null;
  email: string;
  phoneNumber: string | null;
  /** Read-only, from business-profile's own query — see file header. */
  businessName: string | null;
  verification: TrustVerificationStatus;
  accountStatus: AccountStatus | null;
}

// ---------------------------------------------------------------------------
// Connect Code (QR) — a durable, rotatable, opaque token identifying
// THIS account for scanning, distinct from Find Supplier's invitation
// tickets on purpose: invitations are one-time and addressed to a
// specific person; a Connect Code sits on a business card and gets
// scanned by many different people over months, so it can't expire
// after first use the way a ticket does.
//
// OPAQUE BY DESIGN, not merely hidden: the code itself never encodes
// user_id or role — nothing in the string is derivable at all. It only
// means something because a future backend keeps a private
// token_hash -> (user_id, role) lookup, the exact same trust model
// already proven by src/shared/tickets/tickets.py (password reset,
// supplier invitations). Scanning resolves the code SERVER-SIDE; the
// scanning device never learns who it belongs to except through
// whatever the backend chooses to return — including a clear rejection
// when the relationship would be same-role (business-business or
// supplier-supplier), enforced there, not on this screen.
//
// MOCK THIS ROUND: no backend endpoint issues real codes yet. The
// mock generates a random-looking, SESSION-STABLE opaque string (same
// discipline as every other mock in this feature — real UI, mock
// data, resets on app restart) so the actual QR rendering, layout,
// and "regenerate" flow are all genuinely real and reviewable now,
// without pretending server-side issuance exists yet.
// ---------------------------------------------------------------------------

export interface ConnectCode {
  /** Opaque — see this section's own note. Never parse or derive
   *  anything from this value; only the future backend can. */
  token: string;
  createdAt: string;
}

/** Lightweight display name — see this file's own note on
 *  businessName below: this is NOT business identity. It edits
 *  AuthUser's own firstName/lastName, the same real fields Contact
 *  Details already reads (just not, until now, ever written from
 *  here). */
export interface DisplayNameInput {
  firstName: string;
  lastName: string;
}

// ---------------------------------------------------------------------------
// FUTURE BACKEND CONTRACT — file.txt §22. Examples only; names to be
// finalised against real backend conventions once this domain is built
// (the existing auth domain uses /auth/*, kebab-multi-word paths, e.g.
// /auth/phone/request-otp — the closest real precedent for naming).
// DO NOT implement any of these this round.
// ---------------------------------------------------------------------------

/**
 * GET    /auth/me                          — ALREADY REAL, reused as-is
 * PATCH  /account/profile                  — firstName/lastName/bio,
 *                                             and anything else My
 *                                             Account later owns that
 *                                             AuthUser doesn't
 * POST   /account/profile/image            — returns FileAsset (pending)
 * GET    /files/{id}/status                — poll an UploadSession
 * DELETE /files/{id}
 * GET    /account/payment-methods
 * POST   /account/payment-methods
 * DELETE /account/payment-methods/{id}
 * PATCH  /account/payment-methods/{id}/default
 * POST   /account/deactivate
 * POST   /account/delete                   — requires re-auth
 * GET    /account/status                   — accountStatus + suspensionReason
 * GET    /account/connect-code              — current ConnectCode
 * POST   /account/connect-code/regenerate   — invalidates the old one
 * POST   /connect-codes/{token}/resolve     — the scanning side; rejects
 *                                             same-role scans with a
 *                                             clear reason, never just
 *                                             a generic failure
 *
 * NOT under /account/* — proof-of-payment belongs to a specific stock
 * order once the Stock Order feature exists (e.g.
 * POST /stock-orders/{id}/payment-proof), not to My Account. See the
 * note above PaymentMethodType for why this moved out of this file.
 */
