/**
 * Drives the profile-photo and cover-photo upload straight from the
 * Profile screen -- pick (camera/library) -> upload -> the stored url
 * lands on the SupplierProfile cache, no navigation to a separate
 * screen.
 *
 * Replaces the old useProfileImage/useCoverImage hooks (which read a
 * session-only mock in fileRepository.ts). The displayed image now
 * comes from the real profile's businessImageUrl / coverImageUrl --
 * this hook just writes the freshly-stored url into that same cache
 * entry (optimistically, then reconciled against the backend in real
 * mode) so it shows immediately.
 */
import { useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { supplierProfileKey } from "./useAccountProfile";
import type { SupplierProfileData } from "../services/accountService";
import {
  removeProfileImage,
  uploadProfileImage,
  type ProfileImageSlot,
} from "../services/profileImageUpload";
import { pickImage, type ImageSource } from "@/services/media/imagePicker";

const SLOT_FIELD: Record<ProfileImageSlot, "businessImageUrl" | "coverImageUrl"> = {
  profile: "businessImageUrl",
  cover: "coverImageUrl",
};
const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

export function useProfileImageUpload() {
  const queryClient = useQueryClient();
  const [busySlot, setBusySlot] = useState<ProfileImageSlot | null>(null);
  const [error, setError] = useState<string | null>(null);

  const patchProfileCache = useCallback(
    (slot: ProfileImageSlot, url: string | null) => {
      queryClient.setQueryData<SupplierProfileData>(supplierProfileKey, (prev) =>
        prev ? { ...prev, [SLOT_FIELD[slot]]: url } : prev
      );
    },
    [queryClient]
  );

  const pickAndUpload = useCallback(
    async (slot: ProfileImageSlot, source: ImageSource) => {
      if (busySlot) return;
      setError(null);
      const localUri = await pickImage(source);
      if (!localUri) return; // cancelled or permission denied (the picker already explained why)

      setBusySlot(slot);
      try {
        const { secureUrl } = await uploadProfileImage(slot, localUri);
        patchProfileCache(slot, secureUrl);
        if (!USE_MOCK) {
          queryClient.invalidateQueries({ queryKey: supplierProfileKey });
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Couldn't upload that photo. Try again.");
      } finally {
        setBusySlot(null);
      }
    },
    [busySlot, patchProfileCache, queryClient]
  );

  const remove = useCallback(
    async (slot: ProfileImageSlot) => {
      if (busySlot) return;
      setError(null);
      setBusySlot(slot);
      try {
        await removeProfileImage(slot);
        patchProfileCache(slot, null);
        if (!USE_MOCK) {
          queryClient.invalidateQueries({ queryKey: supplierProfileKey });
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Couldn't remove that photo. Try again.");
      } finally {
        setBusySlot(null);
      }
    },
    [busySlot, patchProfileCache, queryClient]
  );

  return { busySlot, error, pickAndUpload, remove };
}
