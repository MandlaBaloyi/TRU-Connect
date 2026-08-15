import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getProfileImage, setProfileImage } from "../services/fileRepository";
import type { FileAsset } from "../types";

const profileImageKey = ["supplierMyAccount", "profileImage"] as const;

export function useProfileImage() {
  const queryClient = useQueryClient();

  const query = useQuery({ queryKey: profileImageKey, queryFn: getProfileImage });

  const mutation = useMutation({
    mutationFn: (asset: FileAsset | null) => setProfileImage(asset).then(() => asset),
    onSuccess: (asset) => queryClient.setQueryData(profileImageKey, asset),
  });

  return {
    profileImage: query.data ?? null,
    isLoading: query.isLoading,
    setProfileImage: mutation.mutateAsync,
  };
}
