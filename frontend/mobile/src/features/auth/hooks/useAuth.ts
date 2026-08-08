import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { authService } from "@/services/auth/authService";
import { secureStorage } from "@/services/storage/secureStorage";
import { STORAGE_KEYS } from "@/constants/config";
import { persistSession } from "../utils/persistSession";
import type { RegisterPayload, SignInPayload } from "../types";

/**
 * React Query mutations composing the auth service with app-level side
 * effects (secure token storage, navigation).
 * Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt §1-3; Auth Hardening
.
 */

export function useSignIn() {
  const router = useRouter();
  return useMutation({
    mutationFn: (payload: SignInPayload) => authService.signIn(payload),
    onSuccess: async (result) => {
      await persistSession(result);
      router.replace("/(dashboard)");
    },
  });
}

export function useRegister() {
  const router = useRouter();
  return useMutation({
    mutationFn: (payload: RegisterPayload) => authService.register(payload),
    onSuccess: async (_result, variables) => {
      // No session to store: the hardened backend issues no tokens for
      // an unverified account. Only remember which email is pending
      // verification, so the OTP screen knows what it's verifying.
      await secureStorage.setItem(STORAGE_KEYS.PENDING_VERIFICATION_EMAIL, variables.email);
      router.push("/(auth)/verify-otp");
    },
  });
}

export function useGoogleSignIn() {
  const router = useRouter();
  return useMutation({
    mutationFn: (idToken: string) => authService.googleSignIn(idToken),
    onSuccess: async (result) => {
      await persistSession(result);
      router.replace("/(dashboard)");
    },
  });
}

export function useLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const refreshToken = await secureStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
      await authService.logout(refreshToken ?? undefined);
    },
    onSettled: async () => {
      // Same reasoning as clearing tokens below, applied to cached data:
      // this must run REGARDLESS of whether the logout API call
      // succeeded, so a network failure during logout can never leave
      // stale data in the cache. Without this, React Query's in-memory
      // cache survives the logout entirely -- the next person to log in
      // on this device would see the PREVIOUS account's customers,
      // balances, and history flash on screen for a moment before their
      // own real data replaces it. Clearing here means there is nothing
      // left to flash: the cache is genuinely empty before the new
      // session's first request ever fires.
      queryClient.removeQueries();

      await secureStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
      await secureStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
      await secureStorage.removeItem(STORAGE_KEYS.USER_ROLE);
      router.replace("/(onboarding)/welcome");
    },
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: (email: string) => authService.forgotPassword(email),
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: (payload: { ticket: string; newPassword: string; confirmPassword: string }) =>
      authService.resetPassword(payload.ticket, payload.newPassword, payload.confirmPassword),
  });
}

export function useValidateResetTicket() {
  return useMutation({
    mutationFn: (ticket: string) => authService.validateResetTicket(ticket),
  });
}