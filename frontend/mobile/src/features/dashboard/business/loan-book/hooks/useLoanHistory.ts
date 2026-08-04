/**
 * useLoanHistory — the full Loan Book activity timeline.
 */

import { useQuery } from "@tanstack/react-query";

import { getLoanHistory } from "../api/loanBookApi";

export const historyKeys = {
  all: ["loanBookHistory"] as const,
};

export function useLoanHistory() {
  const query = useQuery({
    queryKey: historyKeys.all,
    queryFn: getLoanHistory,
  });

  return {
    events: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    isEmpty: !query.isLoading && (query.data?.length ?? 0) === 0,
    refetch: query.refetch,
  };
}
