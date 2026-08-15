/**
 * Edits phone/email. The FIELDS are real (AuthUser, via
 * useCurrentUser -> GET /auth/me); the SAVE is mock. On success this
 * writes directly into useCurrentUser's own cache entry
 * (currentUserKeys.me()) — mirrors business/my-account/hooks/
 * useContactDetails.ts exactly, same reasoning.
 */
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { currentUserKeys } from "@/features/auth/hooks/useCurrentUser";
import type { AuthUser } from "@/features/auth/types";
import { updateContactField, type ContactField } from "../services/accountService";

export function useUpdateContactField() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ field, value }: { field: ContactField; value: string }) => updateContactField(field, value),
    onSuccess: (savedValue, { field }) => {
      queryClient.setQueryData<AuthUser>(currentUserKeys.me(), (current) =>
        current
          ? { ...current, ...(field === "phone" ? { phoneNumber: savedValue } : { email: savedValue }) }
          : current
      );
    },
  });
}
