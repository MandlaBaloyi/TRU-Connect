import React, { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { useBusinessProfile, useBusinessProfileMutations } from "../hooks";
import type { OperatingHistory } from "../types";
import { OPERATING_HISTORY_LABELS } from "../types";
import { ChipSingleSelect } from "../components";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";

const OPTIONS = (Object.keys(OPERATING_HISTORY_LABELS) as OperatingHistory[]).map((value) => ({ value, label: OPERATING_HISTORY_LABELS[value] }));

export default function OperatingHistoryEditScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { profile, isLoading, isError, refetch } = useBusinessProfile();
  const { saveOperatingHistory, isSavingOperatingHistory } = useBusinessProfileMutations();

  const [value, setValue] = useState<OperatingHistory | undefined>();
  const [initialised, setInitialised] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (profile && !initialised) {
      setValue(profile.operatingHistory.yearsOperating);
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
        <ErrorState message="Could not load your operating history." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const handleSave = async () => {
    try {
      await saveOperatingHistory({ yearsOperating: value });
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save. Try again.");
    }
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <ChipSingleSelect label="How long have you been operating?" options={OPTIONS} value={value} onChange={setValue} />
        {error && <Text style={[styles.error, { color: theme.colors.error }]}>{error}</Text>}
        <PrimaryButton onPress={handleSave} loading={isSavingOperatingHistory} disabled={isSavingOperatingHistory}>
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
