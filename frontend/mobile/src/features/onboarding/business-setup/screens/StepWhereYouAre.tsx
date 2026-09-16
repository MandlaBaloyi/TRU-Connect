import React, { useState } from "react";
import { Pressable, StyleSheet, Text } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { useBusinessProfileMutations } from "@/features/dashboard/business/business-profile/hooks";
import { AddressPickerField } from "@/features/dashboard/shared/location-picker/components/AddressPickerField";
import type { DeliveryLocation } from "@/features/dashboard/shared/location-picker/types";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { SetupStepScaffold } from "../components/SetupStepScaffold";
import { rememberLocationSkipped, useRefreshBusinessSetup } from "../hooks/useBusinessSetup";

/**
 * Step three — a pin on a map.
 *
 * THE ONLY SKIPPABLE STEP, and the skip is the important design
 * decision on this screen (V2_18 4.3). This step needs a location
 * permission or a map drag, and blocking a brand-new account behind a
 * permission dialog is the single most expensive place in an app to
 * lose somebody. Skipping costs exactly two rails — "collect near you"
 * and "not ordered from yet" — and the feed can say so on day three,
 * which is a far better conversation than the one that happens at
 * minute one.
 *
 * THE SKIP IS RECORDED ON THE DEVICE, NOT IN A COLUMN. The server's
 * truth is whether a location exists; "they said not now" is a fact
 * about a phone. See useBusinessSetup.rememberLocationSkipped.
 *
 * COORDINATES COME OFF THE MAP WIDGET, NEVER A STORED GEOCODE. That is
 * a standing rule in this codebase — the temporary Mapbox tier is
 * show-don't-store, and permanent storage needs a card and has no free
 * allowance. AddressPickerField is the one component that gets this
 * right, which is why this screen borrows it rather than asking for a
 * typed address.
 *
 * NO STREET ADDRESS IS ASKED FOR, here or anywhere in setup. An
 * informal business frequently does not have one, and "collect near
 * you" needs a point, not a postal line.
 */
export default function StepWhereYouAre() {
  const theme = useTheme();
  const router = useRouter();
  const refreshSetup = useRefreshBusinessSetup();
  const { saveLocation, isSavingLocation } = useBusinessProfileMutations();

  const [pinned, setPinned] = useState<DeliveryLocation | null>(null);
  const [error, setError] = useState<string | null>(null);

  const finish = () => router.replace("/(dashboard)/business/home" as never);

  const handleSave = async () => {
    if (!pinned) return;
    setError(null);
    try {
      await saveLocation({
        latitude: pinned.latitude,
        longitude: pinned.longitude,
        // The geocoder returning nothing is normal for a rural or
        // informal pin, and is not a failure -- the coordinates are
        // what the feed actually uses.
        cityOrTown: pinned.city?.trim() || undefined,
      });
      await refreshSetup();
      finish();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save. Try again.");
    }
  };

  const handleSkip = async () => {
    await rememberLocationSkipped();
    finish();
  };

  return (
    <SetupStepScaffold
      step="whereYouAre"
      title="Where is your shop?"
      why={[
        "This is how we find suppliers close enough for you to collect from, and how far away each one is.",
        "Skipping costs you exactly two things — the \"collect near you\" row and \"suppliers you haven't ordered from\". Everything else in your feed works without it.",
        "We keep a point on a map, not a street address, and no supplier is shown where you are — only how far they are from you.",
      ]}
      primaryLabel="Finish"
      onPrimary={handleSave}
      primaryDisabled={!pinned}
      isSaving={isSavingLocation}
      error={error}
      secondary={
        <Pressable
          onPress={handleSkip}
          style={styles.skip}
          accessibilityRole="button"
          accessibilityLabel="Skip for now"
        >
          <Text style={[styles.skipLabel, { color: theme.colors.onSurfaceVariant }]}>
            Skip for now
          </Text>
        </Pressable>
      }
    >
      <AddressPickerField
        value={pinned}
        onSave={setPinned}
        editLabel="Change your shop's location"
        searchLabel="Search for your area"
        mapLabel="Drop a pin"
        pickerTitle="Where your shop is"
        pickerConfirmLabel="Confirm shop location"
      />
    </SetupStepScaffold>
  );
}

const styles = StyleSheet.create({
  // A TEXT LINK, NOT A SECOND BUTTON. Two buttons of equal weight make
  // skipping look like the recommended half of a choice; a link is
  // findable without being an invitation.
  skip: { alignItems: "center", minHeight: 44, justifyContent: "center", padding: spacing.sm },
  skipLabel: { ...typography.body, fontWeight: "600" },
});
