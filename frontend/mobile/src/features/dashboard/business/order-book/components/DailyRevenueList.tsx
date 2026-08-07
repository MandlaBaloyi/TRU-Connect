import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { DailyRevenueEntry } from "../types";
import { formatRevenueDayLabel } from "../algorithms/dailyRevenue";
import { formatCents } from "../services/orderMapper";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  entries: DailyRevenueEntry[];
}

export function DailyRevenueList({ entries }: Props) {
  const theme = useTheme();

  if (entries.length === 0) {
    return (
      <Text style={[styles.empty, { color: theme.colors.onSurfaceVariant }]}>
        No completed orders yet — money made per day will show up here.
      </Text>
    );
  }

  return (
    <View style={styles.list}>
      {entries.map((entry) => (
        <View key={entry.date} style={styles.row}>
          <View>
            <Text style={[styles.label, { color: theme.colors.onSurface }]}>{formatRevenueDayLabel(entry.date)}</Text>
            <Text style={[styles.meta, { color: theme.colors.onSurfaceVariant }]}>
              {entry.orderCount === 1 ? "1 order" : `${entry.orderCount} orders`}
            </Text>
          </View>
          <Text style={[styles.amount, { color: theme.colors.onSurface }]}>{formatCents(entry.totalCents)}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  list: { gap: spacing.xs },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: spacing.sm, minHeight: 44 },
  label: { ...typography.body, fontWeight: "600" },
  meta: { ...typography.bodySmall },
  amount: { ...typography.h2, fontWeight: "700" },
  empty: { ...typography.body, textAlign: "center", paddingVertical: spacing.xl },
});
