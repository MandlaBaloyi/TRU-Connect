import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getSupplierProfile, requestConnection } from "../services/supplierSearchService";
import type { SupplierProfilePreview } from "../types";

const profileKey = (id: string) => ["findSupplier", "profile", id] as const;

export function useSupplierProfile(id: string) {
  return useQuery({
    queryKey: profileKey(id),
    queryFn: () => getSupplierProfile(id),
    enabled: Boolean(id),
  });
}

export function useRequestConnection(supplierId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => requestConnection(supplierId),
    onSuccess: (connectionStatus) => {
      queryClient.setQueryData<SupplierProfilePreview | null>(profileKey(supplierId), (current) =>
        current ? { ...current, connectionStatus } : current
      );
    },
  });
}
