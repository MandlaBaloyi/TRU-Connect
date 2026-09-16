import React, { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { useBusinessProfile, useBusinessProfileMutations } from "../hooks";
import type { BusinessLocation, OperatingModel, SouthAfricanProvince } from "../types";
import { OPERATING_MODEL_LABELS, PROVINCE_LABELS } from "../types";
import { SingleSelectField } from "@/components/forms/SelectField";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { AddressPickerField } from "@/features/dashboard/shared/location-picker/components/AddressPickerField";
import type { DeliveryLocation } from "@/features/dashboard/shared/location-picker/types";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";

const PROVINCE_OPTIONS = (Object.keys(PROVINCE_LABELS) as SouthAfricanProvince[]).map((value) => ({ value, label: PROVINCE_LABELS[value] }));
const OPERATING_MODEL_OPTIONS = (Object.keys(OPERATING_MODEL_LABELS) as OperatingModel[]).map((value) => ({ value, label: OPERATING_MODEL_LABELS[value] }));

export default function LocationEditScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { profile, isLoading, isError, refetch } = useBusinessProfile();
  const { saveLocation, saveBusinessDetails, isSavingLocation } = useBusinessProfileMutations();

  const [location, setLocation] = useState<BusinessLocation>({});
  const [operatingModel, setOperatingModel] = useState<OperatingModel | undefined>();
  const [initialised, setInitialised] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (profile && !initialised) {
      setLocation(profile.location);
      setOperatingModel(profile.businessDetails.operatingModel);
      setInitialised(true);
    }
  }, [profile, initialised]);

  if (isLoading || !profile) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Could not load your location." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  // THE PICKER SPEAKS DeliveryLocation; the profile stores a flatter
  // shape. Only the coordinates and the town actually matter here -- a
  // shop's profile is not a delivery address, and V2's own rule is
  // never to require a street address from an informal business.
  const pinnedLocation: DeliveryLocation | null =
    location.latitude != null && location.longitude != null
      ? {
          building: "",
          street: location.physicalAddress ?? "",
          suburb: "",
          city: location.cityOrTown ?? "",
          province: "",
          postalCode: "",
          latitude: location.latitude,
          longitude: location.longitude,
        }
      : null;

  const handlePinned = (picked: DeliveryLocation) => {
    setLocation((current) => ({
      ...current,
      latitude: picked.latitude,
      longitude: picked.longitude,
      // WHAT THEY CONFIRMED IS WHAT GETS SAVED -- see the same handler
      // on the My Account profile screen for why the "only when empty"
      // version was wrong: it left the old town on screen after a new
      // pin was confirmed, so the app looked like it had saved an
      // address nobody chose. Falls back to the existing value only
      // when the geocoder returned nothing, which is normal for a rural
      // or informal pin.
      cityOrTown: picked.city?.trim() || current.cityOrTown,
      physicalAddress:
        [picked.building, picked.street, picked.suburb].filter((part) => part?.trim()).join(", ") ||
        current.physicalAddress,
    }));
  };

  const handleSave = async () => {
    try {
      await Promise.all([saveLocation(location), saveBusinessDetails({ operatingModel })]);
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save. Try again.");
    }
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <SingleSelectField label="Province" options={PROVINCE_OPTIONS} value={location.province} onChange={(province) => setLocation({ ...location, province })} placeholder="Tap to choose" />

        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>City, town or area</Text>
          <TextInput
            value={location.cityOrTown ?? ""}
            onChangeText={(text) => setLocation({ ...location, cityOrTown: text })}
            placeholder="e.g. Soweto, Johannesburg"
            placeholderTextColor={theme.colors.onSurfaceVariant}
            style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            accessibilityLabel="City, town or area"
          />
        </View>

        <SingleSelectField label="Where does your business operate?" options={OPERATING_MODEL_OPTIONS} value={operatingModel} onChange={setOperatingModel} placeholder="Tap to choose" />

        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>
            Pin your shop (optional)
          </Text>
          <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>
            Lets us show you suppliers close enough to collect from.
          </Text>
          <AddressPickerField
            value={pinnedLocation}
            onSave={handlePinned}
            editLabel="Edit your shop's location"
            searchLabel="Search address"
            mapLabel="Drop a pin"
            pickerTitle="Where your shop is"
            pickerConfirmLabel="Confirm shop location"
          />
        </View>

        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Physical address (optional)</Text>
          <TextInput
            value={location.physicalAddress ?? ""}
            onChangeText={(text) => setLocation({ ...location, physicalAddress: text })}
            placeholder="Only if you'd like to add more detail"
            placeholderTextColor={theme.colors.onSurfaceVariant}
            style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            accessibilityLabel="Physical address, optional"
          />
        </View>

        {error && <Text style={[styles.error, { color: theme.colors.error }]}>{error}</Text>}

        <PrimaryButton onPress={handleSave} loading={isSavingLocation} disabled={isSavingLocation}>
          Save
        </PrimaryButton>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.lg },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  field: { gap: spacing.xs },
  label: { ...typography.bodySmall, fontWeight: "600" },
  hint: { ...typography.caption },
  input: { borderWidth: 1, borderRadius: 8, paddingHorizontal: spacing.md, minHeight: 48, ...typography.body },
  error: { ...typography.bodySmall },
});
