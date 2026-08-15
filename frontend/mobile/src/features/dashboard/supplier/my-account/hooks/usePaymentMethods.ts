import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  addPaymentMethod,
  getPaymentMethods,
  removePaymentMethod,
  setDefaultPaymentMethod,
} from "../services/paymentMethodsService";
import type { AddPaymentMethodInput } from "../types";

const paymentMethodsKey = ["supplierMyAccount", "paymentMethods"] as const;

export function usePaymentMethods() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: paymentMethodsKey,
    queryFn: getPaymentMethods,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: paymentMethodsKey });

  const addMutation = useMutation({
    mutationFn: (input: AddPaymentMethodInput) => addPaymentMethod(input),
    onSuccess: invalidate,
  });

  const removeMutation = useMutation({
    mutationFn: (id: string) => removePaymentMethod(id),
    onSuccess: invalidate,
  });

  const setDefaultMutation = useMutation({
    mutationFn: (id: string) => setDefaultPaymentMethod(id),
    onSuccess: invalidate,
  });

  return {
    paymentMethods: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    addPaymentMethod: addMutation.mutateAsync,
    isAdding: addMutation.isPending,
    addError: addMutation.error,
    removePaymentMethod: removeMutation.mutateAsync,
    isRemoving: removeMutation.isPending,
    setDefaultPaymentMethod: setDefaultMutation.mutateAsync,
  };
}
