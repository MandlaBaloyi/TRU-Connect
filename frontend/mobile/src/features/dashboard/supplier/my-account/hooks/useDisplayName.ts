/**
 * Edits firstName/lastName. Mirrors business/my-account/hooks/
 * useDisplayName.ts exactly.
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
