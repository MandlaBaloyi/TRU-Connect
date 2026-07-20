import { apiClient } from "@/services/api/apiClient";
import {
  AuthTokens,
  AuthUser,
  RegisterPayload,
  SignInPayload,
  VerifyOtpPayload,
} from "@/features/auth/types";

/**
 * Authentication Domain service -- raw API bindings only. Feature-level
 * hooks (src/features/auth/hooks) compose these calls with React Query and
 * app-level side effects (navigation, storage).
 * Ref: docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.1
 * (Authentication Domain endpoints).
 */
export const authService = {
  async signIn(payload: SignInPayload): Promise<{ user: AuthUser; tokens: AuthTokens }> {
    const { data } = await apiClient.post("/auth/login", payload);
    return data;
  },

  async register(payload: RegisterPayload): Promise<{ user: AuthUser; tokens: AuthTokens }> {
    const { data } = await apiClient.post("/auth/register", payload);
    return data;
  },

  async googleSignIn(idToken: string): Promise<{ user: AuthUser; tokens: AuthTokens }> {
    const { data } = await apiClient.post("/auth/google", { idToken });
    return data;
  },

  async requestOtp(destination: string): Promise<{ success: boolean }> {
    const { data } = await apiClient.post("/auth/phone/request-otp", { destination });
    return data;
  },

  async verifyOtp(payload: VerifyOtpPayload): Promise<{ success: boolean }> {
    const { data } = await apiClient.post("/auth/phone/verify-otp", payload);
    return data;
  },

  async forgotPassword(email: string): Promise<{ success: boolean }> {
    const { data } = await apiClient.post("/auth/forgot-password", { email });
    return data;
  },

  async logout(): Promise<void> {
    await apiClient.post("/auth/logout");
  },
};
