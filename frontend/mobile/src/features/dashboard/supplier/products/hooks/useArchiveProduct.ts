/**
 * useArchiveProduct — Product Detail's own Archive mutation. This
 * flips isArchived to true, nothing else -- a real, permanent removal
 * is a SEPARATE action (useDeleteProduct), soft-deleting the row
 * rather than archiving it. Invalidates the whole feature on success,
 * same reasoning as useCreateProduct: the list screen's Archived
 * filter and product count both need to reflect this immediately, not
 * after a stale cache window.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { archiveProduct } from "../api/productsApi";
import { productsKeys } from "./productsKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useArchiveProduct() {
  const userId = useCurrentUserId();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (productId: string) => archiveProduct(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productsKeys.all(userId) });
    },
  });

  return {
    archiveProduct: mutation.mutateAsync,
    isArchiving: mutation.isPending,
    error: mutation.error,
  };
}
