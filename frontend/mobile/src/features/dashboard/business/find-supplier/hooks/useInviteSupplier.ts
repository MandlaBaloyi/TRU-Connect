import { useMutation } from "@tanstack/react-query";

import { inviteSupplier } from "../services/supplierSearchService";

export function useInviteSupplier() {
  const mutation = useMutation({
    mutationFn: (email: string) => inviteSupplier(email),
  });

  return {
    invite: mutation.mutateAsync,
    isInviting: mutation.isPending,
    isSent: mutation.isSuccess,
    error: mutation.error,
    reset: mutation.reset,
  };
}
