import React, { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { useBusinessProfile, useBusinessProfileMutations } from "../hooks";
import type { BusinessLocation, OperatingModel, SouthAfricanProvince } from "../types";
import { OPERATING_MODEL_LABELS, PROVINCE_LABELS } from "../types";
import { ChipSingleSelect } from "../components";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

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
        <ChipSingleSelect label="Province" options={PROVINCE_OPTIONS} value={location.province} onChange={(province) => setLocation({ ...location, province })} />

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

        <ChipSingleSelect label="Where does your business operate?" options={OPERATING_MODEL_OPTIONS} value={operatingModel} onChange={setOperatingModel} />

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
  input: { borderWidth: 1, borderRadius: 8, paddingHorizontal: spacing.md, minHeight: 48, ...typography.body },
  error: { ...typography.bodySmall },
});
