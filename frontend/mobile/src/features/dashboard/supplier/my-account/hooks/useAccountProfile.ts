/**
 * Assembles everything the landing screen needs. Mirrors
 * business/my-account/hooks/useAccountProfile.ts exactly in shape —
 * reuses the SAME real, shared useCurrentUser() hook (this is
 * genuinely auth-domain, not business- or supplier-specific, so
 * there's nothing to duplicate there) — but businessName comes from
 * this feature's own mock service instead of a real cross-feature
 * peek, since no real "get my own supplier profile" endpoint exists
 * yet (see types.ts's future-contract note).
 *
 * verification -> HARDCODED "NOT_VERIFIED", same fix as the business
 * side, same reasoning — see types.ts's own TrustVerificationStatus
 * docstring. This is the identical bug on this side of the app: email
 * OTP confirmation was never a real supplier-identity check.
 */
import { useQuery } from "@tanstack/react-query";

import { useCurrentUser } from "@/features/auth/hooks/useCurrentUser";
import { getMyBusinessName } from "../services/accountService";
import type { AccountProfileSummary } from "../types";

export function useAccountProfile() {
  const userQuery = useCurrentUser();

  const businessNameQuery = useQuery({
    queryKey: ["supplierMyAccount", "businessName"],
    queryFn: getMyBusinessName,
  });

  const user = userQuery.data;
  const summary: AccountProfileSummary | undefined = user
    ? {
        firstName: user.firstName,
        lastName: user.lastName,
        email: user.email,
        phoneNumber: user.phoneNumber,
        businessName: businessNameQuery.data ?? null,
        verification: "NOT_VERIFIED",
        accountStatus: user.accountStatus,
      }
    : undefined;

  return {
    summary,
    // Only the REAL identity fetch gates the screen — businessName is
    // additive, same non-blocking rule as the business side.
    isLoading: userQuery.isLoading,
    isError: userQuery.isError,
    error: userQuery.error,
    refetch: userQuery.refetch,
  };
}
