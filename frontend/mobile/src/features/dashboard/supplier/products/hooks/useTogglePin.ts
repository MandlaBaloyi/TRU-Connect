/**
 * useTogglePin — the ⋮-menu "Feature on business profile" / "Remove
 * from profile" action on a product card. One mutation, either
 * direction, invalidates the whole feature on success so the list's
 * pin state (and the profile strip, next time it's opened) reflect the
 * change. Rejections (max 6, archived product) surface as the mutation
 * error for the caller to show.
 */
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { pinProduct, unpinProduct } from "../api/productsApi";
import { productsKeys } from "./productsKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useTogglePin() {
  const userId = useCurrentUserId();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: ({ productId, pinned }: { productId: string; pinned: boolean }) =>
      pinned ? pinProduct(productId) : unpinProduct(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productsKeys.all(userId) });
    },
  });

  return {
    togglePin: mutation.mutateAsync,
    isToggling: mutation.isPending,
    error: mutation.error,
  };
}
