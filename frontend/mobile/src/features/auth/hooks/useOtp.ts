import { useMutation } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { authService } from "@/services/auth/authService";
import { persistSession } from "../utils/persistSession";
import type { VerifyOtpPayload } from "../types";

/**
 * OTP verification hooks.
 * Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt §2; Auth Hardening
 * master prompt, Objective 1.
 *
 * Verifying OTP is now the first authenticated moment for a brand-new
 * account -- it's the only place a token pair for that account has ever
 * existed, so this is where the session actually gets persisted.
 */
export function useRequestOtp() {
  return useMutation({
    mutationFn: (destination: string) => authService.requestOtp(destination),
  });
}

export function useVerifyOtp() {
  const router = useRouter();
  return useMutation({
    mutationFn: (payload: VerifyOtpPayload) => authService.verifyOtp(payload),
    onSuccess: async (result) => {
      await persistSession(result);
      router.replace("/(dashboard)");
    },
  });
}