import { useMutation, useQueryClient } from "@tanstack/react-query";

import * as ordersService from "../services/ordersService";

/** Used by both the Stock Catalogue's own product cards and the
 *  product detail screen -- one real "Add to Cart" implementation,
 *  not duplicated per screen. Invalidates the cart query for this
 *  supplier so the cart badge and cart screen both reflect the real,
 *  new state immediately. */
export function useAddToCart(supplierId: string) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: ({ productId, quantity }: { productId: string; quantity: number }) =>
      ordersService.addItem(supplierId, productId, quantity),
    onSuccess: (cart) => {
      queryClient.setQueryData(["orders", "cart", supplierId], cart);
    },
  });

  return {
    addToCart: mutation.mutateAsync,
    isAdding: mutation.isPending,
  };
}
