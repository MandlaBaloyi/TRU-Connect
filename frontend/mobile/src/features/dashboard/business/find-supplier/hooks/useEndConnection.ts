import { useMutation, useQueryClient } from "@tanstack/react-query";

import { endConnection } from "../services/supplierSearchService";
import type { DisconnectReason } from "../types";

export function useEndConnection(supplierId: string) {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: ({ reason, details }: { reason: DisconnectReason; details: string | null }) =>
      endConnection(supplierId, reason, details),
    onSuccess: () => {
      // Invalidates My Connections' own query -- the real point of
      // this whole feature: the supplier genuinely disappears from
      // the active list the moment this succeeds, not just locally in
      // this screen's own state.
      queryClient.invalidateQueries({ queryKey: ["myConnections"] });
    },
  });

  return {
    endConnection: mutation.mutateAsync,
    isEnding: mutation.isPending,
  };
}
