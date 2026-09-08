/**
 * The seam between the supplier portal's auth screens and the backend.
 *
 * NOW WIRED. These used to throw NotWiredError on purpose, because the
 * browser half of authentication did not exist and a form that appears
 * to sign you in and does not is worse than one that says it cannot.
 * Backend step 7 built it: /api/v1/auth/web issues an httpOnly, Secure,
 * SameSite session cookie plus a readable CSRF companion, and enforces
 * the double-submit on every write.
 *
 * THERE IS NO TOKEN IN ANY OF THESE RETURN VALUES, and that is the
 * point rather than an omission. The mobile app stores a JWT and sends
 * `Authorization: Bearer`; a browser must not, because anything
 * JavaScript can read, an XSS on the page can read and exfiltrate. The
 * credential arrives as a cookie this code cannot see, and every
 * subsequent request carries it because api/client.ts sends
 * `credentials: "include"`.
 *
 * WHICH IS WHY session() EXISTS. The portal genuinely cannot tell
 * whether it is signed in by looking -- it has to ask.
 *
 * SIGN-UP IS STILL THE MOBILE ENDPOINT. Registration was never
 * browser-specific: it creates an account and sends an OTP, and issues
 * no session at all (there is no valid session for an unverified
 * account). So it posts to /auth/register like the app does, and the
 * person signs in afterwards.
 */
import { ApiError, api } from "@/api/client";

export interface SupplierSignUpPayload {
  /** The trading name businesses will see. Required. */
  businessName: string;
  /** The person's own name. Optional -- the business name is what matters. */
  ownerName?: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
}

export interface SignInPayload {
  email: string;
  password: string;
}

/**
 * SNAKE_CASE, because that is what the wire actually carries.
 *
 * User.to_public_dict() is shared with the mobile app's /auth/me and
 * emits snake_case. An earlier version of this interface declared
 * camelCase fields that simply never arrive -- TypeScript is perfectly
 * happy with that, because it describes a shape rather than checking
 * one, so the mismatch shows up only as fields silently rendering
 * empty. Verified against a live response before being written this
 * way.
 *
 * NO business_name HERE, for the same reason: to_public_dict does not
 * return one. The supplier's trading name lives on SupplierProfile and
 * is fetched from the profile endpoint, not from the session.
 */
export interface PortalUser {
  id: string;
  email: string;
  role: string;
  verification_status: string;
  account_status: string;
  last_login_at: string | null;
  first_name: string | null;
  profile_image_url: string | null;
}

/**
 * The backend's stable error codes, re-exported so a screen branches on
 * a constant rather than on a matched string. WRONG_PORTAL is the one
 * unique to the web: a business account, correct password, no supplier
 * screens to show them.
 */
export const AUTH_CODES = {
  WRONG_PORTAL: "WRONG_PORTAL",
  EMAIL_NOT_VERIFIED: "EMAIL_NOT_VERIFIED",
  ACCOUNT_LOCKED: "ACCOUNT_LOCKED",
  ACCOUNT_INACTIVE: "ACCOUNT_INACTIVE",
} as const;

/**
 * CAMELCASE KEYS, matching SupplierRegisterSchema's `data_key`s exactly.
 * The Python side is snake_case internally and declares the wire names
 * separately, so `business_name` here would be silently dropped and
 * then rejected as missing -- an error that reads like the form is
 * broken rather than like a key is misspelled.
 *
 * NO PHONE NUMBER. Registration does not collect one: a phone is
 * attached later through the OTP flow, which is a separate, verified
 * step. Sending one here would be ignored.
 */
export async function signUpSupplier(
  payload: SupplierSignUpPayload,
): Promise<void> {
  await api.post("/auth/register", {
    role: "supplier",
    businessName: payload.businessName,
    // Omitted rather than sent empty: the backend treats absent as "no
    // owner name given", and an empty string as a name that is blank.
    ...(payload.ownerName ? { ownerName: payload.ownerName } : {}),
    email: payload.email,
    password: payload.password,
    confirmPassword: payload.confirmPassword,
    acceptTerms: payload.acceptTerms,
  });
}

export async function signIn(payload: SignInPayload): Promise<PortalUser> {
  const data = await api.post<{ user: PortalUser }>("/auth/web/login", payload);
  return data.user;
}

/**
 * Who the cookie says we are, or null.
 *
 * A 401 IS NOT AN ERROR HERE -- it is the answer. Every page load asks
 * this question, and "signed out" is the ordinary case; throwing would
 * make each caller wrap it in a try/catch that means "no".
 */
export async function session(): Promise<PortalUser | null> {
  try {
    const data = await api.get<{ user: PortalUser }>("/auth/web/session");
    return data.user;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null;
    throw error;
  }
}

/**
 * Signs out. NEVER THROWS, deliberately -- the backend's logout is
 * already tolerant of an expired session for the same reason, and a
 * sign-out button that can fail is one someone has to be talked through
 * over the phone. Whatever happened, the caller should send them to the
 * sign-in page.
 */
export async function signOut(): Promise<void> {
  try {
    await api.post("/auth/web/logout");
  } catch {
    // Intentionally swallowed. See above.
  }
}

export { ApiError };
