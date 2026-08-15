import { useQuery } from "@tanstack/react-query";

import { getCustomerRequests } from "../services/customerRequestsService";

export function useCustomerRequests() {
  const query = useQuery({
    queryKey: ["customerRequests", "list"],
    queryFn: getCustomerRequests,
  });

  return {
    requests: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}
