/**
 * Edits phone/email. The FIELDS are real (AuthUser, via useCurrentUser
 * -> GET /auth/me); the SAVE is mock (accountService.updateContactField
 * — no PATCH /account/profile exists yet). On success this writes
 * directly into useCurrentUser's own cache entry (currentUserKeys.me())
 * rather than a separate local field, specifically so the value never
 * reverts to the pre-edit one on the next real-looking fetch — a
 * mismatch there would look like a bug, not an honest "this is mocked"
 * signal. Resets on app restart along with the rest of the mock layer,
 * same as Security's session-persistent mocks.
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
