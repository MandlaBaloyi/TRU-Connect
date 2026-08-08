import React, { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { useBusinessProfile, useBusinessProfileMutations } from "../hooks";
import type { SupplierSource } from "../types";
import { SUPPLIER_SOURCE_LABELS } from "../types";
import { ChipMultiSelect } from "../components";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";

const OPTIONS = (Object.keys(SUPPLIER_SOURCE_LABELS) as SupplierSource[]).map((value) => ({ value, label: SUPPLIER_SOURCE_LABELS[value] }));

export default function SupplierInfoEditScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { profile, isLoading, isError, refetch } = useBusinessProfile();
  const { saveSupplierInfo, isSavingSupplierInfo } = useBusinessProfileMutations();

  const [sources, setSources] = useState<SupplierSource[]>([]);
  const [initialised, setInitialised] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (profile && !initialised) {
      setSources(profile.supplierInfo.sources);
      setInitialised(true);
    }
  }, [profile, initialised]);

  if (isLoading || !profile) {
    return (
      <ScreenContainer>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError) {
    return (
      <ScreenContainer>
        <ErrorState message="Could not load your supplier sourcing." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const handleSave = async () => {
    try {
      await saveSupplierInfo({ sources });
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save. Try again.");
    }
  };

  return (
    <ScreenContainer>
      <ScrollView contentContainerStyle={styles.content}>
        <ChipMultiSelect label="Where do you usually get stock or supplies?" options={OPTIONS} value={sources} onChange={setSources} />
        {error && <Text style={[styles.error, { color: theme.colors.error }]}>{error}</Text>}
        <PrimaryButton onPress={handleSave} loading={isSavingSupplierInfo} disabled={isSavingSupplierInfo}>
          Save
        </PrimaryButton>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.lg },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  error: { ...typography.bodySmall },
});
