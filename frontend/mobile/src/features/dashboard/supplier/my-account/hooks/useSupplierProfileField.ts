import { useSupplierProfile } from "./useSupplierProfile";
import type { SupplierProfileData } from "../services/accountService";

/**
 * Change ONE field on the supplier profile without having to know the
 * shape of the other twenty.
 *
 * WHY THIS EXISTS AS A HOOK AND NOT A LOCAL HELPER. The API is a
 * whole-object PATCH (see useSupplierProfile's own docstring: one
 * SupplierProfile row, one write, never piecemeal saves), so every
 * caller has to send every field, passing through the ones it isn't
 * changing. That pass-through list used to be written out by hand
 * inside ProfileScreen.tsx.
 *
 * That was survivable while the profile was the only screen that
 * wrote. It stopped being survivable when Settings started writing
 * too: two hand-maintained copies of "all the fields" means the next
 * field somebody adds gets silently dropped by whichever copy they
 * forgot — and dropped silently, because the PATCH succeeds and just
 * writes a null over it. One list, one place, no second copy.
 *
 * FAILS LOUDLY IF THE PROFILE ISN'T LOADED. Callers must render a
 * loading state before offering an edit; a save against a null profile
 * would be a write of undefineds, which is exactly the silent data
 * loss this hook exists to prevent.
 */
export function useSupplierProfileField() {
  const { profile, save, isSaving, isLoading, isError, refetch } = useSupplierProfile();

  const saveField = async (patch: Partial<SupplierProfileData>) => {
    if (!profile) {
      throw new Error("Cannot save a profile field before the profile has loaded.");
    }

    return save({
      businessName: profile.businessName,
      category: profile.category,
      location: profile.location,
      description: profile.description,
      photoVisibility: profile.photoVisibility,
      visibleImageSource: profile.visibleImageSource,
      businessImageUrl: profile.businessImageUrl,
      coverImageUrl: profile.coverImageUrl,
      whatsappNumber: profile.whatsappNumber,
      contactEmail: profile.contactEmail,
      tiktokHandle: profile.tiktokHandle,
      shareContactDetails: profile.shareContactDetails,
      offersDelivery: profile.offersDelivery,
      minimumOrderCents: profile.minimumOrderCents,
      collectionBuilding: profile.collectionBuilding,
      collectionStreet: profile.collectionStreet,
      collectionSuburb: profile.collectionSuburb,
      collectionCity: profile.collectionCity,
      collectionProvince: profile.collectionProvince,
      collectionPostalCode: profile.collectionPostalCode,
      collectionLatitude: profile.collectionLatitude,
      collectionLongitude: profile.collectionLongitude,
      showLastActive: profile.showLastActive,
      showTrackRecord: profile.showTrackRecord,
      ...patch,
    });
  };

  return { profile, saveField, isSaving, isLoading, isError, refetch };
}
