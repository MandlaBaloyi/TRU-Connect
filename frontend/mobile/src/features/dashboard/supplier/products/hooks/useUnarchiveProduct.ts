/**
 * useUnarchiveProduct — Product Detail's own Unarchive mutation.
 * Flips isArchived back to false, nothing else. Same invalidate-the-
 * whole-feature reasoning as useArchiveProduct.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { unarchiveProduct } from "../api/productsApi";
import { productsKeys } from "./productsKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useUnarchiveProduct() {
  const userId = useCurrentUserId();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (productId: string) => unarchiveProduct(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productsKeys.all(userId) });
    },
  });

  return {
    unarchiveProduct: mutation.mutateAsync,
    isUnarchiving: mutation.isPending,
    error: mutation.error,
  };
}
