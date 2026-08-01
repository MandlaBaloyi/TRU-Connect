import { apiGet, apiPost } from "@/services/api/apiClient";
import { USE_MOCK_API } from "@/constants/config";
import { mockDelay, MOCK_TOKENS, MOCK_USER } from "@/services/api/mockData";
import type {
  AuthResult,
  AuthTokensApi,
  AuthUser,
  AuthUserApi,
  RegisterPayload,
  RegisterResult,
  SignInPayload,
  VerifyOtpPayload,
} from "@/features/auth/types";

/**
 * Authentication Domain service.
 * Ref: docs/05_BACKEND_API_SPECIFICATION.txt §5.1; Auth Hardening master
 * prompt, Objective 1.
 *
 * register() returns ONLY { user } -- the hardened backend issues no
 * tokens for an unverified account. verifyOtp() now returns
 * { user, tokens } instead: proving control of the email is the first
 * genuinely authenticated moment for a brand-new account.
 */

function mapUser(api: AuthUserApi): AuthUser {
  return {
    id: api.id,
    email: api.email,
    role: api.role,
    firstName: api.first_name,
    lastName: api.last_name,
    phoneNumber: api.phone_number,
    accountStatus: api.account_status,
    verificationStatus: api.verification_status,
    isActive: api.is_active,
    lastLoginAt: api.last_login_at,
    createdAt: api.created_at,
  };
}

function mapAuthResult(payload: { user: AuthUserApi; tokens: AuthTokensApi }): AuthResult {
  return {
    user: mapUser(payload.user),
    tokens: {
      accessToken: payload.tokens.access_token,
      refreshToken: payload.tokens.refresh_token,
    },
  };
}

export const authService = {
  async signIn(payload: SignInPayload): Promise<AuthResult> {
    if (USE_MOCK_API) {
      return mockDelay({ user: { ...MOCK_USER, email: payload.email }, tokens: MOCK_TOKENS });
    }
    const data = await apiPost<{ user: AuthUserApi; tokens: AuthTokensApi }>("/auth/login", payload);
    return mapAuthResult(data);
  },

  async register(payload: RegisterPayload): Promise<RegisterResult> {
    if (USE_MOCK_API) {
      return mockDelay({ user: { ...MOCK_USER, email: payload.email, role: payload.role } });
    }
    // Sent as-is: the backend schemas use data_key to accept this exact
    // camelCase shape, including confirmPassword and the acceptance flags.
    const data = await apiPost<{ user: AuthUserApi }>("/auth/register", payload);
    return { user: mapUser(data.user) };
  },

  async googleSignIn(idToken: string): Promise<AuthResult> {
    if (USE_MOCK_API) return mockDelay({ user: MOCK_USER, tokens: MOCK_TOKENS });
    const data = await apiPost<{ user: AuthUserApi; tokens: AuthTokensApi }>("/auth/google", { idToken });
    return mapAuthResult(data);
  },

  async getCurrentUser(): Promise<AuthUser> {
    if (USE_MOCK_API) return mockDelay(MOCK_USER as unknown as AuthUser);
    const data = await apiGet<AuthUserApi>("/auth/me");
    return mapUser(data);
  },

  async requestOtp(destination: string): Promise<void> {
    if (USE_MOCK_API) return mockDelay(undefined);
    await apiPost("/auth/phone/request-otp", { destination });
  },

  /**
   * Returns the token pair now -- this is the first authenticated
   * moment for a brand-new account (Auth Hardening master prompt,
   * Objective 1).
   */
  async verifyOtp(payload: VerifyOtpPayload): Promise<AuthResult> {
    if (USE_MOCK_API) return mockDelay({ user: MOCK_USER, tokens: MOCK_TOKENS });
    const data = await apiPost<{ user: AuthUserApi; tokens: AuthTokensApi }>("/auth/phone/verify-otp", payload);
    return mapAuthResult(data);
  },

  async forgotPassword(email: string): Promise<void> {
    if (USE_MOCK_API) return mockDelay(undefined);
    await apiPost("/auth/forgot-password", { email });
  },

  async resetPassword(ticket: string, newPassword: string, confirmPassword: string): Promise<void> {
    if (USE_MOCK_API) return mockDelay(undefined);
    await apiPost("/auth/reset-password", { ticket, newPassword, confirmPassword });
  },

  async validateResetTicket(ticket: string): Promise<boolean> {
    if (USE_MOCK_API) return mockDelay(true);
    const data = await apiGet<{ valid: boolean }>(`/auth/reset-password/validate?ticket=${encodeURIComponent(ticket)}`);
    return data.valid;
  },

  async logout(refreshToken?: string): Promise<void> {
    if (USE_MOCK_API) return mockDelay(undefined);
    await apiPost("/auth/logout", refreshToken ? { refresh_token: refreshToken } : {});
  },
};