import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { SetLowStockThresholdInput, StockAdjustmentInput } from "../types";
import { adjustStock, setLowStockThreshold } from "../api/inventoryApi";
import { inventoryKeys } from "./inventoryKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useAdjustStock() {
  const userId = useCurrentUserId();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (input: StockAdjustmentInput) => adjustStock(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryKeys.all(userId) });
    },
  });

  return {
    adjustStock: mutation.mutateAsync,
    isAdjusting: mutation.isPending,
    error: mutation.error,
  };
}

export function useSetLowStockThreshold() {
  const userId = useCurrentUserId();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (input: SetLowStockThresholdInput) => setLowStockThreshold(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryKeys.all(userId) });
    },
  });

  return {
    setLowStockThreshold: mutation.mutateAsync,
    isSettingThreshold: mutation.isPending,
    error: mutation.error,
  };
}
