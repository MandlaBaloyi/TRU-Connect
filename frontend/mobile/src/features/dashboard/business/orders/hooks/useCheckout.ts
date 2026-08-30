import { useMutation, useQueryClient } from "@tanstack/react-query";

import * as ordersService from "../services/ordersService";
import type { SubmitCheckoutRequest } from "../types";

export function useCheckout(supplierId: string) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (request: SubmitCheckoutRequest) => ordersService.submitCheckout(supplierId, request),
    onSuccess: () => {
      // The real cart genuinely clears once submitted -- this
      // supplier's own cart query (and the "My Checkouts" hub list)
      // must both reflect that immediately.
      queryClient.setQueryData(["orders", "cart", supplierId], null);
      queryClient.invalidateQueries({ queryKey: ["orders", "myCarts"] });
    },
  });

  return {
    submitCheckout: mutation.mutateAsync,
    isSubmitting: mutation.isPending,
  };
}
