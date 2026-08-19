import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { InventorySettings } from "../types";
import { getInventorySettings, updateInventorySettings } from "../api/inventoryApi";
import { inventoryKeys } from "./inventoryKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useInventorySettings() {
  const userId = useCurrentUserId();
  const queryClient = useQueryClient();

  const query = useQuery<InventorySettings>({
    queryKey: [...inventoryKeys.all(userId), "settings"],
    queryFn: () => getInventorySettings(),
    enabled: Boolean(userId),
  });

  const mutation = useMutation({
    mutationFn: (input: Partial<InventorySettings>) => updateInventorySettings(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryKeys.all(userId) });
    },
  });

  return {
    settings: query.data,
    isLoading: query.isLoading,
    updateSettings: mutation.mutateAsync,
    isUpdating: mutation.isPending,
    error: mutation.error,
  };
}
