import Constants from "expo-constants";

/**
 * Central app configuration, sourced from app.json `extra` and/or
 * environment variables. Ref: docs/05_BACKEND_API_SPECIFICATION.txt
 */
export const API_BASE_URL: string =
  process.env.EXPO_PUBLIC_API_BASE_URL ||
  (Constants.expoConfig?.extra?.apiBaseUrl as string) ||
  "https://api.truconnect.dev/api/v1";

export const OTP_LENGTH = 6;
export const OTP_RESEND_SECONDS = 60;

export const STORAGE_KEYS = {
  ACCESS_TOKEN: "tru_connect_access_token",
  REFRESH_TOKEN: "tru_connect_refresh_token",
  SELECTED_ROLE: "tru_connect_selected_role",
  ONBOARDING_COMPLETE: "tru_connect_onboarding_complete",
} as const;
