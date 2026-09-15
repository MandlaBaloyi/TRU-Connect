/**
 * Types mirroring the Authentication Domain.
 * Ref: docs/04_DATABASE_DESIGN.txt §4.1, docs/05_BACKEND_API_SPECIFICATION.txt §5.1
 */
export type UserRole = "business" | "supplier" | "admin";

export type AccountStatus = "active" | "suspended" | "deactivated";
export type VerificationStatus = "unverified" | "pending" | "verified";

export interface AuthUser {
  id: string;
  email: string;
  role: UserRole | null;
  firstName: string | null;
  lastName: string | null;
  phoneNumber: string | null;
  accountStatus: AccountStatus | null;
  verificationStatus: VerificationStatus | null;
  isActive: boolean;
  lastLoginAt: string | null;
  createdAt: string | null;
}

/** Raw shape exactly as the backend sends it. Used only by authService. */
export interface AuthUserApi {
  id: string;
  email: string;
  role: UserRole | null;
  first_name: string | null;
  last_name: string | null;
  phone_number: string | null;
  account_status: AccountStatus | null;
  verification_status: VerificationStatus | null;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string | null;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export interface AuthTokensApi {
  access_token: string;
  refresh_token: string;
}

export interface AuthResult {
  user: AuthUser;
  tokens: AuthTokens;
}

/**
 * What POST /auth/register now returns.
 *
 * NO tokens: the hardened backend never issues a session for an
 * unverified account (Auth Hardening master prompt, Objective 1). The
 * first real session comes from verifyOtp() instead, which returns
 * AuthResult.
 */
export interface RegisterResult {
  user: AuthUser;
}

export interface SignInPayload {
  email: string;
  password: string;
}

export interface BusinessRegisterPayload {
  role: "business";
  firstName: string;
  lastName: string;
  /** REQUIRED. It was optional and the backend dropped it, so a shop's
   *  profile was seeded from the owner's personal name — which is the
   *  name a supplier saw when they looked their own customer up in
   *  Find Business. */
  businessName: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptPrivacyPolicy: true;
}

export interface SupplierRegisterPayload {
  role: "supplier";
  businessName: string;
  ownerName?: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptTerms: true;
  // Supplier Invitation (file.txt Phase 2) — present only when this
  // registration was reached via an invitation link. Optional: a
  // missing/expired ticket never blocks registration itself, see the
  // backend's own link_invitation_at_registration docstring.
  invitationTicket?: string;
}

export type RegisterPayload = BusinessRegisterPayload | SupplierRegisterPayload;

export interface VerifyOtpPayload {
  destination: string;
  code: string;
}