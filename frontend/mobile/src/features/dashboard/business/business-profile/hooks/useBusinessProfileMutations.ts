import { useMutation, useQueryClient } from "@tanstack/react-query";

import type {
  BusinessDetails,
  ContactDetails,
  BusinessLocation,
  OperatingHistoryInfo,
  SupplierInfo,
  TradingDetails,
} from "../types";
import {
  updateBusinessDetails,
  updateContactDetails,
  updateLocation,
  updateOperatingHistory,
  updateSupplierInfo,
  updateTradingDetails,
} from "../api/businessProfileApi";
import { businessProfileKeys } from "./businessProfileKeys";
import { useCurrentUserId } from "./useCurrentUserId";

/** Each section saves independently — editing Contact Details never
 *  requires touching, validating, or re-submitting any other section.
 *  Matches the spec's explicit "each section should be independently
 *  editable" requirement. */
export function useBusinessProfileMutations() {
  const userId = useCurrentUserId();
  const queryClient = useQueryClient();

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: businessProfileKeys.profile(userId) });
  };

  const businessDetailsMutation = useMutation({
    mutationFn: (input: Partial<BusinessDetails>) => updateBusinessDetails(input),
    onSuccess: invalidate,
  });
  const contactDetailsMutation = useMutation({
    mutationFn: (input: Partial<ContactDetails>) => updateContactDetails(input),
    onSuccess: invalidate,
  });
  const locationMutation = useMutation({
    mutationFn: (input: Partial<BusinessLocation>) => updateLocation(input),
    onSuccess: invalidate,
  });
  const tradingDetailsMutation = useMutation({
    mutationFn: (input: Partial<TradingDetails>) => updateTradingDetails(input),
    onSuccess: invalidate,
  });
  const operatingHistoryMutation = useMutation({
    mutationFn: (input: Partial<OperatingHistoryInfo>) => updateOperatingHistory(input),
    onSuccess: invalidate,
  });
  const supplierInfoMutation = useMutation({
    mutationFn: (input: Partial<SupplierInfo>) => updateSupplierInfo(input),
    onSuccess: invalidate,
  });

  return {
    saveBusinessDetails: businessDetailsMutation.mutateAsync,
    isSavingBusinessDetails: businessDetailsMutation.isPending,

    saveContactDetails: contactDetailsMutation.mutateAsync,
    isSavingContactDetails: contactDetailsMutation.isPending,

    saveLocation: locationMutation.mutateAsync,
    isSavingLocation: locationMutation.isPending,

    saveTradingDetails: tradingDetailsMutation.mutateAsync,
    isSavingTradingDetails: tradingDetailsMutation.isPending,

    saveOperatingHistory: operatingHistoryMutation.mutateAsync,
    isSavingOperatingHistory: operatingHistoryMutation.isPending,

    saveSupplierInfo: supplierInfoMutation.mutateAsync,
    isSavingSupplierInfo: supplierInfoMutation.isPending,
  };
}
