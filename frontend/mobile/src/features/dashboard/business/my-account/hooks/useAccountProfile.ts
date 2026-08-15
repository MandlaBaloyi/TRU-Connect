/**
 * Assembles everything the My Account profile header needs, from its
 * REAL sources, without three separate loading spinners racing each
 * other on first render (file.txt §26: don't block the whole screen
 * while one optional section loads).
 *
 *   - name/email/phone/accountStatus -> auth's real GET /auth/me
 *     (useCurrentUser) — see types.ts's ownership note.
 *   - businessName -> business-profile's OWN query
 *     (businessProfileKeys.profile), read-only. This deliberately
 *     reuses business-profile's existing query key rather than
 *     inventing a parallel fetch: if the person has already opened My
 *     Business this session, React Query serves this from cache with
 *     no extra network call at all; if not, it's one request with the
 *     project's normal 30s staleTime (queryClient.ts), never polled.
 *     My Account never WRITES to this key — see types.ts's data-
 *     ownership note for why.
 *   - verification -> HARDCODED "NOT_VERIFIED", not derived from
 *     anything. A previous version of this file mapped this from
 *     user.verificationStatus (email-OTP confirmation) — a real bug,
 *     not a naming issue: that field proves someone controls an
 *     inbox, nothing about a real identity/business check. See
 *     types.ts's own TrustVerificationStatus docstring for the full
 *     reasoning. This is the ONE line that changes once real
 *     verification logic exists — nothing downstream needs to.
 *
 * The business name is treated as OPTIONAL and non-blocking: if it
 * hasn't loaded yet, the header still renders with the person's name
 * immediately (isLoading below reflects ONLY the real auth fetch).
 */
import { useQuery } from "@tanstack/react-query";

import { useCurrentUser } from "@/features/auth/hooks/useCurrentUser";
import { getBusinessProfile } from "@/features/dashboard/business/business-profile/api/businessProfileApi";
import { businessProfileKeys } from "@/features/dashboard/business/business-profile/hooks/businessProfileKeys";
import { useCurrentUserId } from "@/features/dashboard/business/business-profile/hooks/useCurrentUserId";
import type { AccountProfileSummary } from "../types";

export function useAccountProfile() {
  const userQuery = useCurrentUser();
  const userId = useCurrentUserId();

  const businessNameQuery = useQuery({
    queryKey: businessProfileKeys.profile(userId),
    queryFn: getBusinessProfile,
    enabled: Boolean(userId),
    // Read-only peek: this feature never invalidates or writes this
    // key — see this file's own docstring.
    select: (profile) => profile.businessDetails.businessName || null,
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
    // Only the REAL identity fetch gates the screen — business name is
    // additive and fills in when it arrives (file.txt §26).
    isLoading: userQuery.isLoading,
    isError: userQuery.isError,
    error: userQuery.error,
    refetch: userQuery.refetch,
  };
}
