import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as ordersService from "../services/ordersService";

/** One cart, one supplier -- matches the real backend's own "one
 *  CART per (business, supplier) pair" guarantee. Update/remove both
 *  invalidate this same query key so the screen always reflects the
 *  real, current state after either mutation. */
export function useCart(supplierId: string) {
  const queryClient = useQueryClient();
  const queryKey = ["orders", "cart", supplierId];

  const query = useQuery({
    queryKey,
    queryFn: () => ordersService.getCart(supplierId),
    enabled: Boolean(supplierId),
  });

  const updateQuantity = useMutation({
    mutationFn: ({ productId, quantity }: { productId: string; quantity: number }) =>
      ordersService.updateItemQuantity(supplierId, productId, quantity),
    onSuccess: (cart) => queryClient.setQueryData(queryKey, cart),
  });

  const remove = useMutation({
    mutationFn: (productId: string) => ordersService.removeItem(supplierId, productId),
    onSuccess: (cart) => queryClient.setQueryData(queryKey, cart),
  });

  return {
    cart: query.data ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    updateQuantity: updateQuantity.mutateAsync,
    isUpdatingQuantity: updateQuantity.isPending,
    removeItem: remove.mutateAsync,
    isRemoving: remove.isPending,
  };
}
