/**
 * Account Security service — THE SINGLE INTEGRATION BOUNDARY.
 *
 * ============================================================
 * READ THIS BEFORE CONNECTING THE BACKEND
 * ============================================================
 * Every function below is backed by in-memory mock state. NO fake
 * HTTP calls are made and NO endpoints are invented — when the backend
 * exists, replace each function body with a real apiGet/apiPost call.
 * The signatures are the contract; the hooks, components and screens
 * above this file need no changes at all.
 *
 * Mock state lives in module scope, so it survives navigation within a
 * session (toggle 2FA, go back, and the new state is still there — as
 * it would be with a real API) but resets on app restart. That's
 * deliberate: persisting security state locally would misrepresent
 * what is actually enforced server-side. NOTHING here is written to
 * storage.
 *
 * SECURITY RULES OBSERVED (spec §18):
 *  - Secrets, OTP codes and tokens are NEVER logged.
 *  - No IP addresses are handled anywhere.
 *  - The authenticator secret is produced for one-time display and
 *    not retained after enrolment.
 */
import type {
  ActiveSession,
  AuthenticatorEnrolment,
  ChangePasswordInput,
  LoginActivityEntry,
  SecurityAlert,
  SecurityOverview,
  TrustedDevice,
  TwoFactorMethod,
  TwoFactorStatus,
} from "../types";

/** Realistic async latency so loading states are genuinely exercised
 *  in development instead of never appearing. */
const latency = () => new Promise<void>((resolve) => setTimeout(resolve, 300));

const daysAgo = (n: number) => new Date(Date.now() - n * 86_400_000).toISOString();
const hoursAgo = (n: number) => new Date(Date.now() - n * 3_600_000).toISOString();

// --- Mock state (module scope; see docstring) --------------------------

let twoFactorState: TwoFactorStatus = { isEnabled: false, activeMethod: null, enabledAt: null };
let passwordLastChangedAt: string | null = daysAgo(94);
let biometricEnabledForApp = false;

let trustedDevices: TrustedDevice[] = [
  { id: "d1", name: "This device", location: "Polokwane, South Africa", lastActiveAt: new Date().toISOString(), isCurrentDevice: true },
  { id: "d2", name: "Samsung Galaxy A14", location: "Polokwane, South Africa", lastActiveAt: daysAgo(6), isCurrentDevice: false },
];

let activeSessions: ActiveSession[] = [
  { id: "s1", deviceName: "This device", location: "Polokwane, South Africa", startedAt: hoursAgo(2), lastActiveAt: new Date().toISOString(), isCurrentSession: true },
  { id: "s2", deviceName: "Samsung Galaxy A14", location: "Polokwane, South Africa", startedAt: daysAgo(6), lastActiveAt: daysAgo(6), isCurrentSession: false },
];

const loginActivity: LoginActivityEntry[] = [
  { id: "l1", deviceName: "This device", location: "Polokwane, South Africa", occurredAt: hoursAgo(2), result: "SUCCESS" },
  { id: "l2", deviceName: "Unrecognised device", location: "Gauteng, South Africa", occurredAt: daysAgo(3), result: "FAILED" },
  { id: "l3", deviceName: "Samsung Galaxy A14", location: "Polokwane, South Africa", occurredAt: daysAgo(6), result: "SUCCESS" },
];

let securityAlerts: SecurityAlert[] = [
  {
    id: "a1",
    title: "Sign-in attempt blocked",
    description:
      "Someone tried to sign in to your account from an unrecognised device and was blocked. If this wasn't you, change your password.",
    severity: "WARNING",
    occurredAt: daysAgo(3),
    isRead: false,
  },
  {
    id: "a2",
    title: "Two-factor authentication is off",
    description: "Turning on two-factor authentication makes your account significantly harder to break into.",
    severity: "INFO",
    occurredAt: daysAgo(10),
    isRead: true,
  },
];

// --- API --------------------------------------------------------------

export async function getSecurityOverview(): Promise<SecurityOverview> {
  await latency();
  return {
    password: { lastChangedAt: passwordLastChangedAt },
    twoFactor: twoFactorState,
    trustedDeviceCount: trustedDevices.length,
    activeSessionCount: activeSessions.length,
    unreadAlertCount: securityAlerts.filter((a) => !a.isRead).length,
  };
}

export async function changePassword(input: ChangePasswordInput): Promise<void> {
  await latency();
  // NEVER log `input` -- it carries plaintext passwords.
  if (!input.currentPassword) {
    throw new Error("Enter your current password.");
  }
  passwordLastChangedAt = new Date().toISOString();
}

export async function startAuthenticatorEnrolment(): Promise<AuthenticatorEnrolment> {
  await latency();
  // Placeholder secret, for UI layout only. The REAL secret must be
  // generated server-side: a client-generated 2FA secret provides no
  // actual security, so this is explicitly a stand-in rather than an
  // implementation.
  const secret = "JBSWY3DPEHPK3PXP";
  return { secret, otpauthUri: `otpauth://totp/TruConnect?secret=${secret}&issuer=TruConnect` };
}

export async function confirmTwoFactor(method: TwoFactorMethod, code: string): Promise<void> {
  await latency();
  // NEVER log `code`.
  if (code.trim().length !== 6) {
    throw new Error("Enter the 6-digit code.");
  }
  twoFactorState = { isEnabled: true, activeMethod: method, enabledAt: new Date().toISOString() };
}

export async function disableTwoFactor(): Promise<void> {
  await latency();
  twoFactorState = { isEnabled: false, activeMethod: null, enabledAt: null };
}

export async function getTwoFactorStatus(): Promise<TwoFactorStatus> {
  await latency();
  return twoFactorState;
}

export async function getTrustedDevices(): Promise<TrustedDevice[]> {
  await latency();
  return trustedDevices;
}

export async function removeTrustedDevice(id: string): Promise<void> {
  await latency();
  trustedDevices = trustedDevices.filter((d) => d.id !== id);
}

export async function getActiveSessions(): Promise<ActiveSession[]> {
  await latency();
  return activeSessions;
}

export async function endSession(id: string): Promise<void> {
  await latency();
  activeSessions = activeSessions.filter((s) => s.id !== id);
}

export async function endAllOtherSessions(): Promise<void> {
  await latency();
  activeSessions = activeSessions.filter((s) => s.isCurrentSession);
}

export async function getLoginActivity(): Promise<LoginActivityEntry[]> {
  await latency();
  return loginActivity;
}

export async function getSecurityAlerts(): Promise<SecurityAlert[]> {
  await latency();
  return securityAlerts;
}

export async function markAlertRead(id: string): Promise<void> {
  await latency();
  securityAlerts = securityAlerts.map((a) => (a.id === id ? { ...a, isRead: true } : a));
}

// --- Biometrics (device-local; genuinely not a backend concern) --------

export function getBiometricEnabledForApp(): boolean {
  return biometricEnabledForApp;
}

export function setBiometricEnabledForApp(enabled: boolean): void {
  biometricEnabledForApp = enabled;
}
