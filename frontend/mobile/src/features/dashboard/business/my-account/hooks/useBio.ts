import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getBio, updateBio } from "../services/accountService";

const bioKey = ["myAccount", "bio"] as const;

export function useBio() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: bioKey,
    queryFn: getBio,
  });

  const mutation = useMutation({
    mutationFn: (bio: string) => updateBio(bio),
    onSuccess: (saved) => {
      queryClient.setQueryData(bioKey, saved);
    },
  });

  return {
    bio: query.data ?? null,
    isLoading: query.isLoading,
    save: mutation.mutateAsync,
    isSaving: mutation.isPending,
    error: mutation.error,
  };
}
