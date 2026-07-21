import { useMutation } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { authService } from "@/services/auth/authService";
import { secureStorage } from "@/services/storage/secureStorage";
import { STORAGE_KEYS } from "@/constants/config";
import { RegisterPayload, SignInPayload } from "../types";

/**
 * React Query mutations composing the auth service with app-level side
 * effects (secure token storage, navigation).
 * Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt, Sections 1-3.
 *
 * NOTE: post-sign-in redirect targets "/(dashboard)" (the role-aware
 * index route added by the dashboard generator), not a specific
 * "/(dashboard)/home" -- the index route reads the stored role and
 * forwards to business/home or supplier/home accordingly.
 */
export function useSignIn() {
  const router = useRouter();
  return useMutation({
    mutationFn: (payload: SignInPayload) => authService.signIn(payload),
    onSuccess: async ({ tokens }) => {
      await secureStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.accessToken);
      await secureStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refreshToken);
      router.replace("/(dashboard)");
    },
  });
}

export function useRegister() {
  const router = useRouter();
  return useMutation({
    mutationFn: (payload: RegisterPayload) => authService.register(payload),
    onSuccess: () => {
      // Registration triggers OTP verification before dashboard access,
      // per the Authentication Flow (docs/01, Screen 6).
      router.push("/(auth)/verify-otp");
    },
  });
}

export function useGoogleSignIn() {
  const router = useRouter();
  return useMutation({
    mutationFn: (idToken: string) => authService.googleSignIn(idToken),
    onSuccess: async ({ tokens }) => {
      await secureStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.accessToken);
      await secureStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refreshToken);
      router.replace("/(dashboard)");
    },
  });
}
