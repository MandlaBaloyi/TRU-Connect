import { useMutation } from "@tanstack/react-query";

import { inviteBusiness } from "../services/businessSearchService";

export function useInviteBusiness() {
  const mutation = useMutation({
    mutationFn: (email: string) => inviteBusiness(email),
  });

  return {
    invite: mutation.mutateAsync,
    isInviting: mutation.isPending,
    isSent: mutation.isSuccess,
    error: mutation.error,
    reset: mutation.reset,
  };
}
