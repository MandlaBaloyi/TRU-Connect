import { secureStorage } from "@/services/storage/secureStorage";
import { STORAGE_KEYS } from "@/constants/config";
import type { AuthResult } from "../types";

/**
 * Persists a token pair + the backend-authoritative role to secure
 * storage. Shared between useSignIn/useGoogleSignIn (useAuth.ts) and
 * useVerifyOtp (useOtp.ts) -- verifying OTP is now the first moment a
 * brand-new account gets a session, so it needs the exact same
 * persistence logic sign-in already uses.
 */
export async function persistSession(result: AuthResult): Promise<void> {
  await secureStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, result.tokens.accessToken);
  await secureStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, result.tokens.refreshToken);

  if (result.user.role) {
    await secureStorage.setItem(STORAGE_KEYS.USER_ROLE, result.user.role);
  }
}