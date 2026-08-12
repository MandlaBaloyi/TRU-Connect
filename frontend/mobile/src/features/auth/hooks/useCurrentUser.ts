/**
 * The CURRENT user's full profile — a thin React Query wrapper around
 * authService.getCurrentUser(), which already calls the real, existing
 * GET /auth/me (see services/auth/authService.ts; USE_MOCK_API only
 * affects whether that call is faked, same as every other auth call).
 *
 * ADDED FOR MY ACCOUNT, but deliberately lives in the auth feature, not
 * my-account/ — this is auth-domain data (the same AuthUser sign-in/
 * register/OTP already produce), not something My Account owns. My
 * Account reads it; it doesn't re-model it. Nothing about auth's own
 * existing screens needed to change for this to exist.
 *
 * No `enabled` guard on a stored token: every screen that will use this
 * lives under app/(dashboard)/**, which is only reachable with a real
 * session, same assumption business-profile's useCurrentUserId already
 * makes for that tree.
 */
import { useQuery } from "@tanstack/react-query";

import { authService } from "@/services/auth/authService";
import type { AuthUser } from "../types";

export const currentUserKeys = {
  me: () => ["auth", "me"] as const,
};

export function useCurrentUser() {
  return useQuery<AuthUser>({
    queryKey: currentUserKeys.me(),
    queryFn: () => authService.getCurrentUser(),
  });
}
