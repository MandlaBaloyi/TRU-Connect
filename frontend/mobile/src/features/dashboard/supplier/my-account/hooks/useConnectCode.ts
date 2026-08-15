import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getConnectCode, regenerateConnectCode } from "../services/accountService";

const connectCodeKey = ["supplierMyAccount", "connectCode"] as const;

export function useConnectCode() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: connectCodeKey,
    queryFn: getConnectCode,
  });

  const regenerate = useMutation({
    mutationFn: regenerateConnectCode,
    onSuccess: (code) => queryClient.setQueryData(connectCodeKey, code),
  });

  return {
    connectCode: query.data ?? null,
    isLoading: query.isLoading,
    regenerate: regenerate.mutateAsync,
    isRegenerating: regenerate.isPending,
  };
}
