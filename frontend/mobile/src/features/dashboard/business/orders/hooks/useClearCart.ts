import { useMutation, useQueryClient } from "@tanstack/react-query";

import * as ordersService from "../services/ordersService";

export function useClearCart(supplierId: string) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => ordersService.clearCart(supplierId),
    onSuccess: (cart) => queryClient.setQueryData(["orders", "cart", supplierId], cart),
  });

  return {
    clearCart: mutation.mutateAsync,
    isClearing: mutation.isPending,
  };
}
