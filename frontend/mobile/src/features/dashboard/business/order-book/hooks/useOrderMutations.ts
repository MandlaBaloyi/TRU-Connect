/**
 * useOrderMutations — every Order Book write.
 *
 * Invalidates the whole feature after any write, same call as Loan
 * Book's useLoanPayments.ts: narrower invalidation would be marginally
 * faster and would eventually leave one screen showing a state that
 * contradicts another. No optimistic update here (unlike payments) —
 * completing/cancelling an order is a deliberate, infrequent action the
 * shop owner confirms on the detail screen, not a counter-side ≤15s
 * action, so the small round-trip wait is fine and simpler to reason
 * about.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { CreateOrderInput } from "../types";
import { cancelOrder, clearAllCompletedNow, completeOrder, createOrder } from "../api/orderBookApi";
import { orderBookKeys } from "./orderBookKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useOrderMutations() {
  const userId = useCurrentUserId();
  const queryClient = useQueryClient();

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: orderBookKeys.all(userId) });
  };

  const createOrderMutation = useMutation({
    mutationFn: (input: CreateOrderInput) => createOrder(input),
    onSuccess: invalidateAll,
  });

  const completeOrderMutation = useMutation({
    mutationFn: (orderId: string) => completeOrder(orderId),
    onSuccess: invalidateAll,
  });

  const cancelOrderMutation = useMutation({
    mutationFn: ({ orderId, reason }: { orderId: string; reason?: string }) => cancelOrder(orderId, reason),
    onSuccess: invalidateAll,
  });

  const clearAllCompletedMutation = useMutation({
    mutationFn: () => clearAllCompletedNow(),
    onSuccess: invalidateAll,
  });

  return {
    createOrder: createOrderMutation.mutateAsync,
    isCreatingOrder: createOrderMutation.isPending,

    completeOrder: completeOrderMutation.mutateAsync,
    isCompletingOrder: completeOrderMutation.isPending,

    cancelOrder: cancelOrderMutation.mutateAsync,
    isCancellingOrder: cancelOrderMutation.isPending,

    /** Manual "Clear all completed" — moves them to Trash immediately,
     *  independent of the auto-clear duration setting. */
    clearAllCompleted: clearAllCompletedMutation.mutateAsync,
    isClearingCompleted: clearAllCompletedMutation.isPending,
  };
}
