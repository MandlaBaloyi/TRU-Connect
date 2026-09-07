import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getSupplierProfile, requestConnection } from "../services/supplierSearchService";
import type { SupplierProfilePreview } from "../types";

const profileKey = (id: string) => ["findSupplier", "profile", id] as const;

/** `enabled` lets a caller hold the request back when it already has
 *  what it needs from somewhere cheaper — see orders/hooks/
 *  useSupplierIdentity, which only reaches for this when the cart
 *  couldn't answer. Defaults to on, so every existing caller is
 *  unchanged. */
export function useSupplierProfile(id: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: profileKey(id),
    queryFn: () => getSupplierProfile(id),
    enabled: Boolean(id) && (options?.enabled ?? true),
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
