import { useQuery } from "@tanstack/react-query";

import type { BusinessProfile } from "../types";
import { getBusinessProfile } from "../api/businessProfileApi";
import { calculateProfileCompletion } from "../algorithms/completionCalculator";
import { businessProfileKeys } from "./businessProfileKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useBusinessProfile() {
  const userId = useCurrentUserId();

  const query = useQuery<BusinessProfile>({
    queryKey: businessProfileKeys.profile(userId),
    queryFn: getBusinessProfile,
    enabled: Boolean(userId),
  });

  const completion = query.data ? calculateProfileCompletion(query.data) : undefined;

  return {
    profile: query.data,
    completion,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
