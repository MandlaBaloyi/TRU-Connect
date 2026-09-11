import type { AuthTokens, AuthUser } from "@/features/auth/types";
// TYPE-ONLY, and it has to be: useDashboardNotifications imports the
// mock data back out of this file. `import type` is erased at compile
// time, so the cycle exists for the typechecker and never at runtime.
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

// Every field AuthUser declares, because a mock that is missing half
// the shape is a mock that lets a screen crash only against the real
// API. `roles: ["business"]` here used to fail typecheck outright --
// the field is `role`, singular, and always has been.
export const MOCK_USER: AuthUser = {
  id: "mock-user-1",
  email: "test@truconnect.dev",
  role: "business",
  firstName: "Test",
  lastName: "User",
  phoneNumber: null,
  accountStatus: "active",
  verificationStatus: "verified",
  isActive: true,
  lastLoginAt: null,
  createdAt: null,
};

export const MOCK_NOTIFICATIONS: DashboardNotification[] = [
  {
    id: "mock-notification-1",
    notificationType: "STOCK_ORDER",
    title: "Order confirmed",
    body: "Zenzele Wholesale confirmed your order of 12 items.",
    isRead: false,
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "mock-notification-2",
    notificationType: "INBOX",
    title: "New connection request",
    body: "Mahlangu Fresh Produce wants to connect with you.",
    isRead: false,
    createdAt: new Date(Date.now() - 26 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "mock-notification-3",
    notificationType: "STOCK_ORDER",
    title: "Delivery on the way",
    body: "Your order is out for delivery.",
    isRead: true,
    createdAt: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

// MOCK_UNREAD_COUNT MATCHES the unread rows above rather than being a
// free-standing number. They are read by two hooks that render on the
// same screen, so a mismatch shows as a badge saying 2 above a list
// with three unread items -- which reads as a bug in the badge.
export const MOCK_UNREAD_COUNT = MOCK_NOTIFICATIONS.filter((n) => !n.isRead).length;