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
 * Whether the "verified supplier" tick is shown at all.
 *
 * OFF BY DEFAULT, AND THAT IS THE POINT. Nothing in the backend ever
 * SETS verification_status -- there is no review flow, no admin action,
 * no service that awards it; the column defaults to UNVERIFIED and only
 * a manual SQL update has ever changed it. A verification badge is the
 * strongest trust signal on a supplier's profile, and a business may
 * part with real money partly because of it, so showing one the
 * platform cannot actually stand behind is not a cosmetic stub.
 *
 * Set EXPO_PUBLIC_SHOW_VERIFICATION_BADGE=true locally to demo it.
 * DELETE this flag (and this comment) once a real verification flow
 * exists -- at that point the tick means something and should always
 * show.
 */
export const SHOW_VERIFICATION_BADGE = process.env.EXPO_PUBLIC_SHOW_VERIFICATION_BADGE === "true";

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
  return SHOW_VERIFICATION_BADGE && verificationStatus?.toLowerCase() === "verified";
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