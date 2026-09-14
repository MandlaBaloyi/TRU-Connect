import React, { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { useBusinessProfile, useBusinessProfileMutations } from "../hooks";
import type {
  EmployeeRange,
  RestockRhythm,
  TradingDetails as TradingDetailsType,
  WeeklySpendBand,
} from "../types";
import {
  CUSTOMER_TYPE_LABELS,
  EMPLOYEE_RANGE_LABELS,
  RESTOCK_RHYTHM_LABELS,
  WEEKLY_SPEND_BAND_LABELS,
} from "../types";
import { CATEGORY_OPTIONS } from "@/constants/productCategories";
import { ChipMultiSelect, ChipSingleSelect } from "../components";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";

const CUSTOMER_TYPE_OPTIONS = (Object.keys(CUSTOMER_TYPE_LABELS) as (keyof typeof CUSTOMER_TYPE_LABELS)[]).map((value) => ({ value, label: CUSTOMER_TYPE_LABELS[value] }));
// THE REAL TAXONOMY, not a second list to keep in step. These are the
// same seventeen categories the catalogue, the chips and the feed use.
const BUYS_OPTIONS = CATEGORY_OPTIONS.map((o) => ({ value: o.value as string, label: o.label }));
const RESTOCK_OPTIONS = (Object.keys(RESTOCK_RHYTHM_LABELS) as RestockRhythm[]).map((value) => ({ value, label: RESTOCK_RHYTHM_LABELS[value] }));
const SPEND_OPTIONS = (Object.keys(WEEKLY_SPEND_BAND_LABELS) as WeeklySpendBand[]).map((value) => ({ value, label: WEEKLY_SPEND_BAND_LABELS[value] }));
const EMPLOYEE_OPTIONS = (Object.keys(EMPLOYEE_RANGE_LABELS) as EmployeeRange[]).map((value) => ({ value, label: EMPLOYEE_RANGE_LABELS[value] }));

const EMPTY: TradingDetailsType = { buysCategories: [], customerTypes: [], operatingDays: [] };

/**
 * "What do you sell?" and "When do you usually trade?" were removed
 * from this screen per direct feedback. The underlying
 * products/operatingDays fields still exist on TradingDetails (not
 * touched in types.ts) and are still saved untouched with whatever
 * value they already held — this is a UI removal only, not a data
 * model change, so nothing already saved is lost.
 */
export default function TradingDetailsEditScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { profile, isLoading, isError, refetch } = useBusinessProfile();
  const { saveTradingDetails, isSavingTradingDetails } = useBusinessProfileMutations();

  const [draft, setDraft] = useState<TradingDetailsType>(EMPTY);
  const [initialised, setInitialised] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (profile && !initialised) {
      setDraft(profile.tradingDetails);
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
        <ErrorState message="Could not load your trading details." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const handleSave = async () => {
    try {
      await saveTradingDetails(draft);
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save. Try again.");
    }
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {/* THE MOST IMPORTANT QUESTION ON THIS SCREEN, and it asks what
            they BUY rather than what they sell. It is the only answer
            that changes what the Community feed shows them. */}
        <ChipMultiSelect label="What stock do you buy?" options={BUYS_OPTIONS} value={draft.buysCategories} onChange={(buysCategories) => setDraft({ ...draft, buysCategories })} />
        <ChipMultiSelect label="Who do you mainly sell to?" options={CUSTOMER_TYPE_OPTIONS} value={draft.customerTypes} onChange={(customerTypes) => setDraft({ ...draft, customerTypes })} />
        {/* One tap each, and together they let the feed be useful before
            a single order exists -- see docs/v2/V2_15 Book Three. */}
        <ChipSingleSelect label="How often do you restock?" options={RESTOCK_OPTIONS} value={draft.restockRhythm} onChange={(v) => setDraft({ ...draft, restockRhythm: (v as RestockRhythm) || undefined })} />
        <ChipSingleSelect label="Roughly what do you spend on stock a week?" options={SPEND_OPTIONS} value={draft.weeklySpendBand} onChange={(v) => setDraft({ ...draft, weeklySpendBand: (v as WeeklySpendBand) || undefined })} />

        <View style={styles.timeRow}>
          <View style={[styles.field, { flex: 1 }]}>
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Opening time (optional)</Text>
            <TextInput
              value={draft.openingTime ?? ""}
              onChangeText={(text) => setDraft({ ...draft, openingTime: text })}
              placeholder="08:00"
              placeholderTextColor={theme.colors.onSurfaceVariant}
              style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            />
          </View>
          <View style={[styles.field, { flex: 1 }]}>
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Closing time (optional)</Text>
            <TextInput
              value={draft.closingTime ?? ""}
              onChangeText={(text) => setDraft({ ...draft, closingTime: text })}
              placeholder="17:00"
              placeholderTextColor={theme.colors.onSurfaceVariant}
              style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            />
          </View>
        </View>

        <ChipSingleSelect label="How many people work in the business? (optional)" options={EMPLOYEE_OPTIONS} value={draft.employeeRange} onChange={(employeeRange) => setDraft({ ...draft, employeeRange })} />

        {error && <Text style={[styles.error, { color: theme.colors.error }]}>{error}</Text>}

        <PrimaryButton onPress={handleSave} loading={isSavingTradingDetails} disabled={isSavingTradingDetails}>
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
  timeRow: { flexDirection: "row", gap: spacing.md },
  input: { borderWidth: 1, borderRadius: 8, paddingHorizontal: spacing.md, minHeight: 48, ...typography.body },
  error: { ...typography.bodySmall },
});
