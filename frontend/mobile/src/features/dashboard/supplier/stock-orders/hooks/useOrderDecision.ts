import { useMutation, useQueryClient } from "@tanstack/react-query";

import * as stockOrdersService from "../services/stockOrdersService";
import type { CancelReason, DeclineReason } from "../types";

/** Every real decision a supplier can make on one order -- approve,
 *  decline, and now cancel -- sharing one hook since all three need
 *  the exact same cache invalidation.
 *
 * FIXED A REAL BUG while adding cancel here: the previous version
 * invalidated ["supplier", "stock-orders", "pending"] -- but
 * useOrders' own real query key is ["supplier", "stock-orders",
 * status] where status is the actual StockOrderStatus value
 * ("PENDING_SUPPLIER_APPROVAL" etc.), never the literal word
 * "pending". That key never matched any real cached query, so
 * approving or declining an order was silently NOT invalidating the
 * New-queue list -- it likely only ever appeared to work because
 * staleTime: 0 on useOrders means most navigations refetch anyway.
 * Invalidating the bare ["supplier", "stock-orders"] prefix instead
 * is a genuine React Query partial match -- it catches every tab's
 * query regardless of which status it's keyed on, not just one. */
export function useOrderDecision(orderId: string) {
  const queryClient = useQueryClient();

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["supplier", "stock-orders"] });
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

  const cancel = useMutation({
    mutationFn: ({ reason, details }: { reason: CancelReason; details?: string }) =>
      stockOrdersService.cancelOrder(orderId, reason, details),
    onSuccess: invalidate,
  });

  return {
    approveOrder: approve.mutateAsync,
    isApproving: approve.isPending,
    declineOrder: decline.mutateAsync,
    isDeclining: decline.isPending,
    cancelOrder: cancel.mutateAsync,
    isCancelling: cancel.isPending,
  };
}
