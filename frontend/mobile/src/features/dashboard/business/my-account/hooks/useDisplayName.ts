/**
 * Edits firstName/lastName. The FIELDS are real (AuthUser, via
 * useCurrentUser -> GET /auth/me); the SAVE is mock — no PATCH exists
 * yet. Mirrors hooks/useContactDetails.ts exactly: on success this
 * writes directly into useCurrentUser's own cache entry so the value
 * never reverts to the pre-edit one on the next real-looking fetch.
 */
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { currentUserKeys } from "@/features/auth/hooks/useCurrentUser";
import type { AuthUser } from "@/features/auth/types";
import { updateDisplayName } from "../services/accountService";
import type { DisplayNameInput } from "../types";

export function useUpdateDisplayName() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: DisplayNameInput) => updateDisplayName(input),
    onSuccess: (saved) => {
      queryClient.setQueryData<AuthUser>(currentUserKeys.me(), (current) =>
        current ? { ...current, firstName: saved.firstName, lastName: saved.lastName || null } : current
      );
    },
  });
}
