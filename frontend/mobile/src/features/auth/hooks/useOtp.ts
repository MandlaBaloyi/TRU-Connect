import { useMutation } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { authService } from "@/services/auth/authService";
import { VerifyOtpPayload } from "../types";

/** Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt, Section 2 (Verification) */
export function useRequestOtp() {
  return useMutation({
    mutationFn: (destination: string) => authService.requestOtp(destination),
  });
}

export function useVerifyOtp() {
  const router = useRouter();
  return useMutation({
    mutationFn: (payload: VerifyOtpPayload) => authService.verifyOtp(payload),
    onSuccess: () => {
      // After verification, the user proceeds to complete their Business
      // Profile Setup wizard (docs/01, Screen 7).
      router.replace("/(business)/profile-setup/step-1-business-info");
    },
  });
}
