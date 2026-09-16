/**
 * Business Details — dedicated edit screen. Own route
 * (my-business/business-details), own back button, own Save — matches
 * how the rest of this app handles "add or edit something real" rather
 * than an inline accordion form.
 */

import React, { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { useBusinessProfile, useBusinessProfileMutations } from "../hooks";
import type { BusinessCategory, BusinessType } from "../types";
import { BUSINESS_CATEGORY_LABELS, BUSINESS_TYPE_LABELS } from "../types";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SingleSelectField } from "@/components/forms/SelectField";

const CATEGORY_OPTIONS = (Object.keys(BUSINESS_CATEGORY_LABELS) as BusinessCategory[]).map((value) => ({
  value,
  label: BUSINESS_CATEGORY_LABELS[value],
}));
const TYPE_OPTIONS = (Object.keys(BUSINESS_TYPE_LABELS) as BusinessType[]).map((value) => ({
  value,
  label: BUSINESS_TYPE_LABELS[value],
}));
const DESCRIPTION_MAX_LENGTH = 250;

export default function BusinessDetailsEditScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { profile, isLoading, isError, refetch } = useBusinessProfile();
  const { saveBusinessDetails, isSavingBusinessDetails } = useBusinessProfileMutations();

  const [businessName, setBusinessName] = useState(profile?.businessDetails.businessName ?? "");
  const [category, setCategory] = useState<BusinessCategory | undefined>(profile?.businessDetails.category);
  const [businessType, setBusinessType] = useState<BusinessType | undefined>(profile?.businessDetails.businessType);
  const [description, setDescription] = useState(profile?.businessDetails.description ?? "");
  const [error, setError] = useState<string | null>(null);
  const [initialised, setInitialised] = useState(false);

  // Seed local state once the profile has actually loaded — avoids a
  // render where every field is blank before the fetch resolves.
  useEffect(() => {
    if (profile && !initialised) {
      setBusinessName(profile.businessDetails.businessName);
      setCategory(profile.businessDetails.category);
      setBusinessType(profile.businessDetails.businessType);
      setDescription(profile.businessDetails.description ?? "");
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
        <ErrorState message="Could not load your business details." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const handleSave = async () => {
    if (businessName.trim().length === 0) {
      setError("Give your business a name.");
      return;
    }
    try {
      await saveBusinessDetails({ businessName, category, businessType, description });
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save. Try again.");
    }
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Business name</Text>
          <TextInput
            value={businessName}
            onChangeText={setBusinessName}
            placeholder="e.g. Mandla's Perfumes"
            placeholderTextColor={theme.colors.onSurfaceVariant}
            style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            accessibilityLabel="Business name"
          />
        </View>

        <SingleSelectField label="What type of business do you run?" options={CATEGORY_OPTIONS} value={category} onChange={setCategory} />
        <SingleSelectField label="What type of business is this?" options={TYPE_OPTIONS} value={businessType} onChange={setBusinessType} />

        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Tell us about your business (optional)</Text>
          <TextInput
            value={description}
            onChangeText={(text) => setDescription(text.slice(0, DESCRIPTION_MAX_LENGTH))}
            placeholder="What does your business do?"
            placeholderTextColor={theme.colors.onSurfaceVariant}
            multiline
            style={[styles.input, styles.multiline, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            accessibilityLabel="Business description"
          />
          <Text style={[styles.charCount, { color: theme.colors.onSurfaceVariant }]}>
            {description.length}/{DESCRIPTION_MAX_LENGTH}
          </Text>
        </View>

        {error && <Text style={[styles.error, { color: theme.colors.error }]}>{error}</Text>}

        <PrimaryButton onPress={handleSave} loading={isSavingBusinessDetails} disabled={isSavingBusinessDetails}>
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
  multiline: { minHeight: 80, paddingTop: spacing.sm, textAlignVertical: "top" },
  charCount: { ...typography.caption, textAlign: "right" },
  error: { ...typography.bodySmall },
});
