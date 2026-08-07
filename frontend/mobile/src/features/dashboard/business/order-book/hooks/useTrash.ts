import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { TrashedCustomer, TrashedOrder } from "../types";
import {
  deleteCustomer,
  deleteOrder,
  getTrash,
  restoreCustomer,
  restoreOrder,
} from "../api/orderBookApi";
import { orderBookKeys } from "./orderBookKeys";
import { useCurrentUserId } from "./useCurrentUserId";

export function useTrash() {
  const userId = useCurrentUserId();
  const queryClient = useQueryClient();

  const query = useQuery<{ orders: TrashedOrder[]; customers: TrashedCustomer[] }>({
    queryKey: orderBookKeys.trash(userId),
    queryFn: getTrash,
    enabled: Boolean(userId),
  });

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: orderBookKeys.all(userId) });
  };

  const restoreOrderMutation = useMutation({
    mutationFn: (orderId: string) => restoreOrder(orderId),
    onSuccess: invalidateAll,
  });

  const restoreCustomerMutation = useMutation({
    mutationFn: (customerId: string) => restoreCustomer(customerId),
    onSuccess: invalidateAll,
  });

  const deleteOrderMutation = useMutation({
    mutationFn: (orderId: string) => deleteOrder(orderId),
    onSuccess: invalidateAll,
  });

  const deleteCustomerMutation = useMutation({
    mutationFn: (customerId: string) => deleteCustomer(customerId),
    onSuccess: invalidateAll,
  });

  return {
    trashedOrders: query.data?.orders ?? [],
    trashedCustomers: query.data?.customers ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,

    restoreOrder: restoreOrderMutation.mutateAsync,
    isRestoringOrder: restoreOrderMutation.isPending,
    restoreCustomer: restoreCustomerMutation.mutateAsync,
    isRestoringCustomer: restoreCustomerMutation.isPending,

    deleteOrder: deleteOrderMutation.mutateAsync,
    isDeletingOrder: deleteOrderMutation.isPending,
    deleteCustomer: deleteCustomerMutation.mutateAsync,
    isDeletingCustomer: deleteCustomerMutation.isPending,
  };
}
