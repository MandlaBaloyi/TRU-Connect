import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getMyProfile, updateMyProfile, type SupplierProfileData } from "../services/accountService";
import { supplierProfileKey } from "./useAccountProfile";

/**
 * The one real read/write path for the supplier's own profile --
 * replaces the old separate useBio()/useSupplierBusinessName() mocks,
 * matching how the real backend actually works: one SupplierProfile
 * row, one PATCH updates all of it together, never piecemeal saves.
 *
 * Shares supplierProfileKey with useAccountProfile.ts's own query --
 * a successful save here writes directly into that same cache entry,
 * so the landing screen's own businessName/bio peek reflects a change
 * immediately, without a second network round trip.
 */
export function useSupplierProfile() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: supplierProfileKey,
    queryFn: getMyProfile,
  });

  const mutation = useMutation({
    mutationFn: (input: SupplierProfileData) => updateMyProfile(input),
    onSuccess: (saved) => queryClient.setQueryData(supplierProfileKey, saved),
  });

  return {
    profile: query.data ?? null,
    isLoading: query.isLoading,
    // isError/refetch are exposed so a caller can render a RECOVERABLE
    // failure. Without refetch the only escape from a failed load is
    // backing out of the screen, which on a settings screen means a
    // supplier cannot reach their own privacy switches at all after
    // one bad request.
    isError: query.isError,
    refetch: query.refetch,
    save: mutation.mutateAsync,
    isSaving: mutation.isPending,
  };
}
