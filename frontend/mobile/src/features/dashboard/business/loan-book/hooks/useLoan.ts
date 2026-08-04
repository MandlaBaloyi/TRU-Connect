/**
 * useLoan — a single credit-sale entry with its full payment history.
 */

import { useQuery } from "@tanstack/react-query";

import type { CustomerView, LoanEntryView } from "../types";
import { getCustomerView, getLoanEntry } from "../api/loanBookApi";
import { loanBookKeys } from "./loanBookKeys";

export function useLoan(entryId: string) {
  const query = useQuery<LoanEntryView | null>({
    queryKey: loanBookKeys.entry(entryId),
    queryFn: () => getLoanEntry(entryId),
    enabled: Boolean(entryId),
  });

  return {
    loan: query.data ?? undefined,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    /** Distinguishes "deleted / bad link" from "still loading" — a
     *  missing entry should say so, not spin forever. */
    notFound: !query.isLoading && query.data === null,
    refetch: query.refetch,
  };
}

export function useCustomer(customerId: string) {
  const query = useQuery<CustomerView | null>({
    queryKey: loanBookKeys.customer(customerId),
    queryFn: () => getCustomerView(customerId),
    enabled: Boolean(customerId),
  });

  return {
    customer: query.data ?? undefined,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    notFound: !query.isLoading && query.data === null,
    refetch: query.refetch,
  };
}
