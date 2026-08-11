/**
 * BalancesScreen — "how am I doing today" comes first. Thin on
 * purpose: every piece here lives in its own file.
 *   - TodayBalanceCard (component) + getTodayEntry (algorithm)
 *   - "View more balances" -> its own screen (PerformanceScreen)
 *   - AutoClearAccordion (component), one for completed orders and one
 *     for cancelled orders, both collapsed by default so settings never
 *     compete with the money figure for attention
 * Adding the next brainstormed thing here should mean a new
 * component/service file and one line in this screen, not growing this
 * file itself.
 */

import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { useDailyRevenue, useAutoClearSettings } from "../hooks";
import { getTodayEntry } from "../algorithms/dailyRevenue";
import { TodayBalanceCard, AutoClearAccordion } from "../components";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { SecondaryButton } from "@/components/ui/SecondaryButton";

export default function BalancesScreen() {
  const router = useRouter();
  const theme = useTheme();
  const { entries, isLoading, isError, refetch } = useDailyRevenue();
  const { completedSetting, cancelledSetting, setSetting, isLoading: isSettingLoading } = useAutoClearSettings();

  if (isLoading || isSettingLoading) {
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
        <ErrorState message="Could not load balances." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const today = getTodayEntry(entries);

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <TodayBalanceCard totalCents={today.totalCents} completedCount={today.orderCount} />

        <View style={styles.performanceLink}>
          <Text style={[styles.performanceHint, { color: theme.colors.onSurfaceVariant }]}>
            Order history / performance
          </Text>
          <SecondaryButton onPress={() => router.push("/business/order-book/performance")}>
            View more balances
          </SecondaryButton>
        </View>

        <View style={[styles.divider, { backgroundColor: theme.colors.outline }]} />

        <AutoClearAccordion
          scope="COMPLETED"
          setting={completedSetting}
          onChange={(next) => setSetting("COMPLETED", next)}
        />
        <AutoClearAccordion
          scope="CANCELLED"
          setting={cancelledSetting}
          onChange={(next) => setSetting("CANCELLED", next)}
        />
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.lg },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  performanceLink: { gap: spacing.sm },
  performanceHint: { ...typography.bodySmall },
  divider: { height: StyleSheet.hairlineWidth },
});
