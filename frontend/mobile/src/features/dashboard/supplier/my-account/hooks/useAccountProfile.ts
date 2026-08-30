/**
 * Assembles everything the landing screen needs. Mirrors
 * business/my-account/hooks/useAccountProfile.ts exactly in shape —
 * reuses the SAME real, shared useCurrentUser() hook (this is
 * genuinely auth-domain, not business- or supplier-specific, so
 * there's nothing to duplicate there) — businessName and bio both come
 * from the real GET /supplier-discovery/my-profile now (see
 * accountService.ts's own getMyProfile), the first real read this
 * feature has ever had for either.
 *
 * verification -> HARDCODED "NOT_VERIFIED", same fix as the business
 * side, same reasoning — see types.ts's own TrustVerificationStatus
 * docstring. This is the identical bug on this side of the app: email
 * OTP confirmation was never a real supplier-identity check.
 */
import { useQuery } from "@tanstack/react-query";

import { useCurrentUser } from "@/features/auth/hooks/useCurrentUser";
import { getMyProfile } from "../services/accountService";
import type { AccountProfileSummary } from "../types";

export const supplierProfileKey = ["supplierMyAccount", "profile"] as const;

export function useAccountProfile() {
  const userQuery = useCurrentUser();

  const profileQuery = useQuery({
    queryKey: supplierProfileKey,
    queryFn: getMyProfile,
  });

  const user = userQuery.data;
  const summary: AccountProfileSummary | undefined = user
    ? {
        firstName: user.firstName,
        lastName: user.lastName,
        email: user.email,
        phoneNumber: user.phoneNumber,
        businessName: profileQuery.data?.businessName ?? null,
        bio: profileQuery.data?.description ?? null,
        verification: "NOT_VERIFIED",
        accountStatus: user.accountStatus,
      }
    : undefined;

  return {
    summary,
    // Only the REAL identity fetch gates the screen — the supplier
    // profile peek is additive, same non-blocking rule as the
    // business side.
    isLoading: userQuery.isLoading,
    isError: userQuery.isError,
    error: userQuery.error,
    refetch: userQuery.refetch,
  };
}
