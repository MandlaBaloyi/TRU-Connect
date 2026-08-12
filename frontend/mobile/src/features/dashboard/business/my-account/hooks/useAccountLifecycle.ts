/**
 * Deactivation/deletion REQUEST submission only — never a status
 * toggle. See accountService.ts's own docstring: accountStatus itself
 * is read-only, straight from useCurrentUser(), and nothing here ever
 * touches it. This hook exists purely so the Danger Zone screens have
 * a "request submitted" / "not submitted" state to render, matching
 * file.txt §17/§21's requirement to build the UI and contract without
 * pretending enforcement exists.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getDeactivationRequestStatus,
  getDeletionRequestStatus,
  requestAccountDeletion,
  requestDeactivation,
} from "../services/accountService";
import type { DeleteAccountInput } from "../types";

const deactivationKey = ["myAccount", "deactivationRequest"] as const;
const deletionKey = ["myAccount", "deletionRequest"] as const;

export function useDeactivationRequest() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: deactivationKey, queryFn: getDeactivationRequestStatus });
  const mutation = useMutation({
    mutationFn: requestDeactivation,
    onSuccess: (status) => queryClient.setQueryData(deactivationKey, status),
  });
  return {
    status: query.data ?? "NONE",
    isLoading: query.isLoading,
    submit: mutation.mutateAsync,
    isSubmitting: mutation.isPending,
    error: mutation.error,
  };
}

export function useDeletionRequest() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: deletionKey, queryFn: getDeletionRequestStatus });
  const mutation = useMutation({
    mutationFn: (input: DeleteAccountInput) => requestAccountDeletion(input),
    onSuccess: (status) => queryClient.setQueryData(deletionKey, status),
  });
  return {
    status: query.data ?? "NONE",
    isLoading: query.isLoading,
    submit: mutation.mutateAsync,
    isSubmitting: mutation.isPending,
    error: mutation.error,
  };
}
