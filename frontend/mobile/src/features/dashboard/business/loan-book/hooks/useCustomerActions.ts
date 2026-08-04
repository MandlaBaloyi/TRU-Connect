/**
 * useCustomerActions — customer-level delete/restore mutations.
 * Separate from useLoanPayments (entry/payment mutations) since these
 * operate at a different scope (a whole customer account, not one
 * purchase).
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { deleteCustomer } from "../api/loanBookApi";
import { loanBookKeys } from "./loanBookKeys";
import { trashKeys } from "./useTrash";

export function useCustomerActions() {
  const queryClient = useQueryClient();

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: loanBookKeys.all });
    queryClient.invalidateQueries({ queryKey: trashKeys.all });
  };

  const deleteCustomerMutation = useMutation({
    mutationFn: ({ customerId, reason }: { customerId: string; reason?: string }) =>
      deleteCustomer(customerId, reason),
    onSuccess: invalidateAll,
  });

  return {
    deleteCustomer: deleteCustomerMutation.mutateAsync,
    isDeletingCustomer: deleteCustomerMutation.isPending,
  };
}
