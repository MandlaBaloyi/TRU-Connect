/**
 * useCreateProduct — Add Product's own mutation. Invalidates the whole
 * feature after a successful create, same call as Order Book's
 * useOrderMutations: narrower invalidation would be marginally faster
 * and would eventually leave the list screen showing a stale count
 * right after a create.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { CreateProductInput } from "../types";
import { createProduct } from "../api/productsApi";
import { productsKeys } from "./productsKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useCreateProduct() {
  const userId = useCurrentUserId();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (input: CreateProductInput) => createProduct(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productsKeys.all(userId) });
    },
  });

  return {
    createProduct: mutation.mutateAsync,
    isCreating: mutation.isPending,
    error: mutation.error,
    reset: mutation.reset,
  };
}
