import { useQuery } from "@tanstack/react-query";

import { getSupplierRequests } from "../services/supplierRequestsService";

export function useSupplierRequests() {
  const query = useQuery({
    queryKey: ["supplierRequests", "list"],
    queryFn: getSupplierRequests,
  });

  return {
    requests: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}
