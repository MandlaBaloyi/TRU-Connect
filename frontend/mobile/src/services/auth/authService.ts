/** import { apiClient } from "@/services/api/apiClient";
import {
  AuthTokens,
  AuthUser,
  RegisterPayload,
  SignInPayload,
  VerifyOtpPayload,
} from "@/features/auth/types";


 * Authentication Domain service -- raw API bindings only. Feature-level
 * hooks (src/features/auth/hooks) compose these calls with React Query and
 * app-level side effects (navigation, storage).
 * Ref: docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.1
 * (Authentication Domain endpoints).
 
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
 **/




/*MOCK DATA FOR TESTING  */
import { apiClient } from "@/services/api/apiClient";
import { USE_MOCK_API } from "@/constants/config";
import { mockDelay, MOCK_TOKENS, MOCK_USER } from "@/services/api/mockData";
import {
  AuthTokens,
  AuthUser,
  RegisterPayload,
  SignInPayload,
  VerifyOtpPayload,
} from "@/features/auth/types";

/**
 * Authentication Domain service. In MOCK MODE (USE_MOCK_API), every
 * method resolves successfully with fake data regardless of input --
 * this lets sign-in/registration/OTP be tested end-to-end with no
 * backend running. See src/services/api/mockData.ts.
 * Ref: docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.1.
 */
export const authService = {
  async signIn(payload: SignInPayload): Promise<{ user: AuthUser; tokens: AuthTokens }> {
    if (USE_MOCK_API) return mockDelay({ user: { ...MOCK_USER, email: payload.email }, tokens: MOCK_TOKENS });
    const { data } = await apiClient.post("/auth/login", payload);
    return data;
  },

  async register(payload: RegisterPayload): Promise<{ user: AuthUser; tokens: AuthTokens }> {
    if (USE_MOCK_API) return mockDelay({ user: { ...MOCK_USER, email: payload.email, roles: [payload.role] }, tokens: MOCK_TOKENS });
    const { data } = await apiClient.post("/auth/register", payload);
    return data;
  },

  async googleSignIn(idToken: string): Promise<{ user: AuthUser; tokens: AuthTokens }> {
    if (USE_MOCK_API) return mockDelay({ user: MOCK_USER, tokens: MOCK_TOKENS });
    const { data } = await apiClient.post("/auth/google", { idToken });
    return data;
  },

  async requestOtp(destination: string): Promise<{ success: boolean }> {
    if (USE_MOCK_API) return mockDelay({ success: true });
    const { data } = await apiClient.post("/auth/phone/request-otp", { destination });
    return data;
  },

  async verifyOtp(payload: VerifyOtpPayload): Promise<{ success: boolean }> {
    if (USE_MOCK_API) return mockDelay({ success: true });
    const { data } = await apiClient.post("/auth/phone/verify-otp", payload);
    return data;
  },

  async forgotPassword(email: string): Promise<{ success: boolean }> {
    if (USE_MOCK_API) return mockDelay({ success: true });
    const { data } = await apiClient.post("/auth/forgot-password", { email });
    return data;
  },

  async logout(): Promise<void> {
    if (USE_MOCK_API) return mockDelay(undefined);
    await apiClient.post("/auth/logout");
  },
};