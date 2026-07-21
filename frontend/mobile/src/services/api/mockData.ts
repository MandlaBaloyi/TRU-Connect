import type { AuthTokens, AuthUser } from "@/features/auth/types";

import type { DashboardNotification } from "@/features/dashboard/shared/hooks/useDashboardNotifications";

/**
 * MOCK MODE data. Used only when USE_MOCK_API is true (src/constants/
 * config.ts) -- lets the full app flow (auth -> OTP -> profile wizard ->
 * dashboard) be tested end-to-end with no backend running. Accepts ANY
 * input (any email/password/OTP code) and always "succeeds". Switch
 * USE_MOCK_API to false once the Flask backend (docs/05) is live.
 */

export function mockDelay<T>(value: T, ms = 600): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

export const MOCK_TOKENS: AuthTokens = {
  accessToken: "mock-access-token",
  refreshToken: "mock-refresh-token",
};

export const MOCK_USER: AuthUser = {
  id: "mock-user-1",
  email: "test@truconnect.dev",
  roles: ["business"],
  isActive: true,
};



export const MOCK_UNREAD_COUNT = 2;