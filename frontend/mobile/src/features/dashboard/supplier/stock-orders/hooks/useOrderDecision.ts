import { useMutation, useQueryClient } from "@tanstack/react-query";

import * as stockOrdersService from "../services/stockOrdersService";
import type { DeclineReason } from "../types";

/** Both real decisions a supplier can make on one order, sharing one
 *  hook since both need the exact same cache invalidation -- the
 *  pending list and this order's own detail view must both reflect
 *  the real, new state immediately. */
export function useOrderDecision(orderId: string) {
  const queryClient = useQueryClient();

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["supplier", "stock-orders", "pending"] });
    queryClient.invalidateQueries({ queryKey: ["supplier", "stock-orders", "detail", orderId] });
  };

  const approve = useMutation({
    mutationFn: () => stockOrdersService.approveOrder(orderId),
    onSuccess: invalidate,
  });

  const decline = useMutation({
    mutationFn: ({ reason, details }: { reason: DeclineReason; details?: string }) =>
      stockOrdersService.declineOrder(orderId, reason, details),
    onSuccess: invalidate,
  });

  return {
    approveOrder: approve.mutateAsync,
    isApproving: approve.isPending,
    declineOrder: decline.mutateAsync,
    isDeclining: decline.isPending,
  };
}
