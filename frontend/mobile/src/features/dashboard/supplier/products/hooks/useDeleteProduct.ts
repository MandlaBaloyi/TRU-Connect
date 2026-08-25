/**
 * useDeleteProduct — Product Detail's own Delete mutation. A real,
 * permanent removal from the supplier's own point of view -- soft-
 * deleted on the backend (never actually removed from the database,
 * kept intact for future analysis), but the product vanishes from
 * every screen immediately, same as archive's own invalidation
 * reasoning, just one level more final.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { deleteProduct } from "../api/productsApi";
import { productsKeys } from "./productsKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useDeleteProduct() {
  const userId = useCurrentUserId();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (productId: string) => deleteProduct(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productsKeys.all(userId) });
    },
  });

  return {
    deleteProduct: mutation.mutateAsync,
    isDeleting: mutation.isPending,
    error: mutation.error,
  };
}
