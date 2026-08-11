/**
 * PerformanceScreen — the rollup view. Thin: period state and the pure
 * calc both live in usePerformanceStats.ts / algorithms/performanceStats.ts.
 */

import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import { useTheme } from "react-native-paper";

import { usePerformanceStats } from "../hooks";
import { PERFORMANCE_PERIOD_LABELS } from "../types";
import { PerformancePeriodSelector, PerformanceStatsCard } from "../components";
import { spacing } from "@/theme/spacing";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";

export default function PerformanceScreen() {
  const theme = useTheme();
  const { stats, period, setPeriod, isLoading, isError, refetch } = usePerformanceStats();

  if (isLoading) {
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
        <ErrorState message="Could not load performance." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <PerformancePeriodSelector period={period} onChange={setPeriod} />
        <PerformanceStatsCard stats={stats} periodLabel={PERFORMANCE_PERIOD_LABELS[period]} />
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.lg },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
});
