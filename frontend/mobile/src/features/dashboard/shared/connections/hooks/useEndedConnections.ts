import { useQuery } from "@tanstack/react-query";

import { getEndedConnections } from "../services/connectionsService";

export function useEndedConnections() {
  const query = useQuery({
    queryKey: ["endedConnections"],
    queryFn: getEndedConnections,
  });

  return {
    connections: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}
