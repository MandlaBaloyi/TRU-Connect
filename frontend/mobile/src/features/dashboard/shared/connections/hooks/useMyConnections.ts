import { useQuery } from "@tanstack/react-query";

import { getMyConnections } from "../services/connectionsService";

export function useMyConnections() {
  const query = useQuery({
    queryKey: ["myConnections"],
    queryFn: getMyConnections,
  });

  return {
    connections: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}
