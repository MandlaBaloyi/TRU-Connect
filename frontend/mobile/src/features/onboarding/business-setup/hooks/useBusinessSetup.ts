import { useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { STORAGE_KEYS } from "@/constants/config";
import { secureStorage } from "@/services/storage/secureStorage";

import { getSetupState } from "../api/businessSetupApi";
import type { SetupState } from "../types";

export const businessSetupKeys = {
  all: ["business-setup"] as const,
  state: () => [...businessSetupKeys.all, "state"] as const,
};

/**
 * Whether this shop still owes the demand engine its answers.
 *
 * STALE TIME IS ZERO AND THAT IS DELIBERATE. Each step writes through
 * a different mutation and then immediately asks this again to decide
 * where to go next; a cached answer would send somebody back to the
 * step they just finished. The call is one indexed row read.
 */
export function useBusinessSetup() {
  const query = useQuery<SetupState>({
    queryKey: businessSetupKeys.state(),
    queryFn: getSetupState,
    staleTime: 0,
  });

  return {
    setup: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}

/** Invalidate after a step saves, so the next screen reads the truth
 *  rather than the answer from before the save. */
export function useRefreshBusinessSetup() {
  const queryClient = useQueryClient();
  return useCallback(
    () => queryClient.invalidateQueries({ queryKey: businessSetupKeys.state() }),
    [queryClient]
  );
}

/**
 * The one skip, stored on the device.
 *
 * NOT A COLUMN, AND NOT A LIE. The server records whether a location
 * exists and nothing else; this records that somebody was asked and
 * said not now. Those are different facts about different things —
 * one about a business, one about a phone — and folding the second
 * into the first would mean the backend claiming to know something it
 * cannot.
 *
 * SECURE STORAGE RATHER THAN AsyncStorage only because that is the one
 * storage seam this app has. Nothing here is a secret.
 */
export async function hasSkippedLocation(): Promise<boolean> {
  try {
    return (await secureStorage.getItem(STORAGE_KEYS.SETUP_LOCATION_SKIPPED)) === "true";
  } catch {
    // A READ THAT THROWS MEANS "NOT SKIPPED", which sends somebody to
    // a screen they can skip again -- annoying. The other default
    // would let a storage fault silently hide the step forever, which
    // is worse and invisible.
    return false;
  }
}

export async function rememberLocationSkipped(): Promise<void> {
  try {
    await secureStorage.setItem(STORAGE_KEYS.SETUP_LOCATION_SKIPPED, "true");
  } catch {
    // Non-fatal on purpose. If this fails the person is asked again
    // next launch, which is a worse experience and not a broken one --
    // and failing the skip itself would trap them on the step they
    // were trying to leave.
  }
}
