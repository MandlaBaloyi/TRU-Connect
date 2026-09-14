/**
 * Central app configuration.
 * Ref: docs/05_BACKEND_API_SPECIFICATION.txt
 */
import Constants from "expo-constants";

/**
 * Base URL of the Flask backend.
 *
 * On a physical device, "localhost" refers to the PHONE, not your
 * development machine — use your machine's LAN IP
 * (Windows: `ipconfig` → IPv4 Address), e.g.
 *     http://192.168.1.42:5000/api/v1
 * Flask must be running with host="0.0.0.0" (app.py already does this).
 */
export const API_BASE_URL: string =
  process.env.EXPO_PUBLIC_API_BASE_URL ||
  (Constants.expoConfig?.extra?.apiBaseUrl as string) ||
  "http://10.4.176.99:5000/api/v1";

/**
 * MOCK MODE. When true, auth calls return fake data instantly instead of
 * hitting API_BASE_URL. Set EXPO_PUBLIC_USE_MOCK_API=false in .env to
 * talk to the real backend.
 */
export const USE_MOCK_API = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

/**
 * Mapbox's DEFAULT PUBLIC token -- safe to embed client-side by design
 * (Mapbox's own public tokens are read-only, meant for exactly this).
 * Used only to render the interactive map inside MapPickerModal's
 * WebView -- the SEPARATE backend token (MAPBOX_BACKEND_TOKEN) that
 * does the actual reverse-geocode lookup never reaches this app at
 * all, let alone the client bundle.
 */
export const MAPBOX_PUBLIC_TOKEN: string =
  process.env.EXPO_PUBLIC_MAPBOX_TOKEN || (Constants.expoConfig?.extra?.mapboxPublicToken as string) || "";


/**
 * THE FLAG IS GONE, ON ITS OWN INSTRUCTIONS.
 *
 * It read: "DELETE this flag (and this comment) once a real
 * verification flow exists -- at that point the tick means something
 * and should always show." It was off because nothing in the backend
 * ever SET verification_status: no review flow, no admin action, only
 * a manual SQL update. Showing the strongest trust signal in the app
 * when the platform could not stand behind it was not a cosmetic stub.
 *
 * THAT IS NO LONGER TRUE. verification/services/verification_service.py
 * awards and revokes the status for real, through `flask verification
 * approve` / `revoke`, with an audit trail and a capability check --
 * and the curtain (verification/visibility.py) already makes an
 * unverified supplier invisible to buyers entirely. So the tick now
 * means what it says.
 *
 * WHICH MAKES IT WEAKER ON A RAIL THAN IT LOOKS, worth knowing before
 * adding it everywhere: since the curtain hides unverified suppliers,
 * every supplier a business can see is verified, so a tick in a feed
 * rail is true of 100% of cards. It earns its place on a PROFILE,
 * where somebody arriving from a shared link is asking the question.
 */

/** The one place "should this look verified" is decided, so the flag
 *  can't be honoured in three places and forgotten in a fourth.
 *
 *  CASE-INSENSITIVE, because it is reached from two different shapes
 *  of the same fact: the business-facing discovery payloads send the
 *  enum value ("verified"), while the supplier's own account summary
 *  sends it upper-cased ("VERIFIED"). The supplier-side screens had
 *  been comparing that upper-case form inline and so bypassed the flag
 *  entirely -- a supplier saw a verified tick on their own profile
 *  that no business would ever see, which is the precise misleading
 *  trust signal the flag exists to prevent, pointed at the one person
 *  who would act on it hardest. Normalising here rather than at each
 *  call site keeps this the only place that decides. */
export function showsAsVerified(verificationStatus: string | null | undefined): boolean {
  return verificationStatus?.toLowerCase() === "verified";
}

export const OTP_LENGTH = 6;
export const OTP_RESEND_SECONDS = 60;

export const STORAGE_KEYS = {
  ACCESS_TOKEN: "tru_connect_access_token",
  REFRESH_TOKEN: "tru_connect_refresh_token",

  /** Role chosen during onboarding (before an account exists). */
  SELECTED_ROLE: "tru_connect_selected_role",

  /**
   * Authoritative role returned by the backend after register/login.
   * This — not SELECTED_ROLE — decides which dashboard the user sees,
   * because a returning user signing in on a fresh install never passes
   * through the onboarding role picker.
   */
  USER_ROLE: "tru_connect_user_role",

  /** Email awaiting OTP verification, carried from register → OTP screen. */
  PENDING_VERIFICATION_EMAIL: "tru_connect_pending_verification_email",

  ONBOARDING_COMPLETE: "tru_connect_onboarding_complete",
} as const;