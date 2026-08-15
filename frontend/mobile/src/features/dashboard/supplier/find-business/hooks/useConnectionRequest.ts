import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getBusinessProfile, requestConnection } from "../services/businessSearchService";
import type { BusinessProfilePreview } from "../types";

const profileKey = (id: string) => ["findBusiness", "profile", id] as const;

export function useBusinessProfile(id: string) {
  return useQuery({
    queryKey: profileKey(id),
    queryFn: () => getBusinessProfile(id),
    enabled: Boolean(id),
  });
}

export function useRequestConnection(businessId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => requestConnection(businessId),
    onSuccess: (connectionStatus) => {
      queryClient.setQueryData<BusinessProfilePreview | null>(profileKey(businessId), (current) =>
        current ? { ...current, connectionStatus } : current
      );
    },
  });
}
