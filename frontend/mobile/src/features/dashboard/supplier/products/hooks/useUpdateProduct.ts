/**
 * useUpdateProduct — Edit Product's own mutation. Invalidates the
 * whole feature on success, same reasoning as useCreateProduct/
 * useArchiveProduct: the list screen and this exact product's detail
 * view both need the fresh values immediately.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { UpdateProductInput } from "../types";
import { updateProduct } from "../api/productsApi";
import { productsKeys } from "./productsKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useUpdateProduct() {
  const userId = useCurrentUserId();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (input: UpdateProductInput) => updateProduct(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productsKeys.all(userId) });
    },
  });

  return {
    updateProduct: mutation.mutateAsync,
    isUpdating: mutation.isPending,
    error: mutation.error,
  };
}
