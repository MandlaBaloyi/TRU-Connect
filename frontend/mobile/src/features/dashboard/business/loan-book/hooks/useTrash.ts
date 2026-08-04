/**
 * useTrash — deleted customers and entries still within the recovery
 * window, plus restore mutations.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getTrash, restoreCustomer, restoreLoanEntry } from "../api/loanBookApi";
import { loanBookKeys } from "./loanBookKeys";

export const trashKeys = {
  all: ["loanBookTrash"] as const,
};

export function useTrash() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: trashKeys.all,
    queryFn: getTrash,
  });

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: trashKeys.all });
    queryClient.invalidateQueries({ queryKey: loanBookKeys.all });
  };

  const restoreEntryMutation = useMutation({
    mutationFn: (entryId: string) => restoreLoanEntry(entryId),
    onSuccess: invalidateAll,
  });

  const restoreCustomerMutation = useMutation({
    mutationFn: (customerId: string) => restoreCustomer(customerId),
    onSuccess: invalidateAll,
  });

  return {
    deletedCustomers: query.data?.customers ?? [],
    deletedEntries: query.data?.entries ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    isEmpty:
      !query.isLoading &&
      (query.data?.customers.length ?? 0) === 0 &&
      (query.data?.entries.length ?? 0) === 0,
    refetch: query.refetch,
    restoreEntry: restoreEntryMutation.mutateAsync,
    isRestoringEntry: restoreEntryMutation.isPending,
    restoreCustomer: restoreCustomerMutation.mutateAsync,
    isRestoringCustomer: restoreCustomerMutation.isPending,
  };
}
