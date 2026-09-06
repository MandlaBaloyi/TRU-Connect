import { useMutation, useQueryClient } from "@tanstack/react-query";

import * as ordersService from "../services/ordersService";
import type { CancelReason } from "../types";

/** The business's own self-service cancel -- only ever succeeds while
 *  PENDING_SUPPLIER_APPROVAL (see the backend's own
 *  cancellation_service.cancel_order_by_business for the full
 *  reasoning). Invalidates both this order's own detail view and the
 *  history list it appears in, same "both places must reflect the
 *  real new state immediately" reasoning as useOrderDecision's own
 *  invalidation on the supplier side. */
export function useCancelOrder(supplierId: string, orderId: string) {
  const queryClient = useQueryClient();

  const cancel = useMutation({
    mutationFn: ({ reason, details }: { reason: CancelReason; details?: string }) =>
      ordersService.cancelOrder(supplierId, orderId, reason, details),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders", "detail", supplierId, orderId] });
      queryClient.invalidateQueries({ queryKey: ["orders", "history", supplierId] });
    },
  });

  return {
    cancelOrder: cancel.mutateAsync,
    isCancelling: cancel.isPending,
  };
}
