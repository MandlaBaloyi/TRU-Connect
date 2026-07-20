/**
 * Types mirroring the Authentication Domain (docs/04_DATABASE_DESIGN.txt,
 * Section 4.1) and the Business/Supplier Domains' account-facing fields.
 */
export type UserRole = "business" | "supplier";

export interface AuthUser {
  id: string;
  email: string;
  phoneNumber?: string;
  roles: UserRole[];
  isActive: boolean;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export interface SignInPayload {
  email: string;
  password: string;
}

/**
 * Deliberately minimal at registration -- SA ID number, mobile number,
 * and registration number are collected later in the Business Profile
 * Setup wizard (app/(business)/profile-setup/*), once the user is
 * already inside the app. This keeps sign-up itself to the fewest
 * possible steps.
 */
export interface BusinessRegisterPayload {
  role: "business";
  firstName: string;
  lastName: string;
  businessName?: string;
  email: string;
  password: string;
}

export interface SupplierRegisterPayload {
  role: "supplier";
  businessName?: string;
  ownerName: string;
  email: string;
  password: string;
}

export type RegisterPayload = BusinessRegisterPayload | SupplierRegisterPayload;

export interface VerifyOtpPayload {
  destination: string; // phone number or email the OTP was sent to
  code: string;
}