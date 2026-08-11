/**
 * Account Security — domain types.
 *
 * FRONTEND-ONLY PHASE. These types define the CONTRACT the backend
 * will later implement. Nothing here invents an endpoint that exists:
 * every value is currently served by a local mock (see
 * services/securityService.ts), and each type is shaped the way a real
 * security API would return it, so wiring the backend later is a
 * service-layer swap rather than a UI rewrite.
 *
 * SECURITY UX RULES BAKED INTO THESE TYPES (per spec §18):
 *  - No raw device identifiers. Devices are identified to the USER by
 *    a friendly name; the opaque `id` is never displayed.
 *  - No IP addresses anywhere in these types, deliberately — the spec
 *    forbids showing them, so the frontend simply never receives one
 *    and cannot leak it by accident.
 *  - No secrets: authenticator secrets, OTPs and tokens are NEVER
 *    stored in these types or persisted by this feature.
 */

/** How far along the user is with 2FA. */
export type TwoFactorMethod = "AUTHENTICATOR" | "EMAIL";

export interface TwoFactorStatus {
  isEnabled: boolean;
  /** null when 2FA has never been enabled. */
  activeMethod: TwoFactorMethod | null;
  /** ISO date, null if never enabled. */
  enabledAt: string | null;
}

export interface PasswordStatus {
  /** ISO date of the last successful password change, null if the
   *  password has never been changed since sign-up. */
  lastChangedAt: string | null;
}

export type BiometricKind = "FINGERPRINT" | "FACE" | "IRIS" | "NONE";

export interface BiometricStatus {
  /** Whether the DEVICE has biometric hardware at all. */
  isAvailable: boolean;
  /** Whether the user has actually enrolled a fingerprint/face on the
   *  device. Hardware can exist with nothing enrolled. */
  isEnrolled: boolean;
  /** What kind the device offers, for accurate copy ("Use fingerprint"
   *  vs "Use face recognition") rather than a vague "Use biometrics". */
  kind: BiometricKind;
  /** Whether the USER has turned biometric sign-in on for TruConnect.
   *  Distinct from isAvailable/isEnrolled — a device can support it
   *  while the user has chosen not to use it here. */
  isEnabledForApp: boolean;
}

export interface TrustedDevice {
  /** Opaque. NEVER displayed — see this file's header. */
  id: string;
  /** Human-friendly, e.g. "Samsung Galaxy A54". */
  name: string;
  /** Coarse location only, e.g. "Johannesburg, South Africa". Never an
   *  IP address. */
  location: string | null;
  lastActiveAt: string;
  /** True for the device the user is holding right now — that one
   *  must never be presented as removable in a way that locks them
   *  out unexpectedly. */
  isCurrentDevice: boolean;
}

export interface ActiveSession {
  id: string;
  deviceName: string;
  location: string | null;
  startedAt: string;
  lastActiveAt: string;
  isCurrentSession: boolean;
}

export type LoginActivityResult = "SUCCESS" | "FAILED";

export interface LoginActivityEntry {
  id: string;
  deviceName: string;
  location: string | null;
  occurredAt: string;
  result: LoginActivityResult;
}

export type SecurityAlertSeverity = "INFO" | "WARNING" | "CRITICAL";

export interface SecurityAlert {
  id: string;
  title: string;
  description: string;
  severity: SecurityAlertSeverity;
  occurredAt: string;
  /** Whether the user has acknowledged/read it. */
  isRead: boolean;
}

/** Everything the Account Security landing screen needs, in one
 *  object — so that screen makes ONE call rather than six. */
export interface SecurityOverview {
  password: PasswordStatus;
  twoFactor: TwoFactorStatus;
  trustedDeviceCount: number;
  activeSessionCount: number;
  unreadAlertCount: number;
}

export interface ChangePasswordInput {
  currentPassword: string;
  newPassword: string;
}

/** Result of starting authenticator-app enrolment. The secret is
 *  returned ONCE, held in memory for the duration of the setup flow
 *  only, and never persisted by the frontend (spec §18: never log or
 *  store authenticator secrets). */
export interface AuthenticatorEnrolment {
  /** The base32 secret, shown once for manual entry. */
  secret: string;
  /** otpauth:// URI a QR code would encode. */
  otpauthUri: string;
}
