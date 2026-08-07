import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { PerformanceStats } from "../types";
import { formatCents } from "../services/orderMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  stats: PerformanceStats;
  periodLabel: string;
}

export function PerformanceStatsCard({ stats, periodLabel }: Props) {
  const theme = useTheme();
  return (
    <View style={[styles.card, { backgroundColor: theme.colors.surface }]}>
      <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Total made · {periodLabel}</Text>
      <Text style={[styles.total, { color: theme.colors.onSurface }]}>{formatCents(stats.totalCents)}</Text>

      <View style={[styles.grid, { borderTopColor: theme.colors.outline }]}>
        <View style={styles.stat}>
          <Text style={[styles.statValue, { color: theme.colors.onSurface }]}>{stats.orderCount}</Text>
          <Text style={[styles.statLabel, { color: theme.colors.onSurfaceVariant }]}>Completed orders</Text>
        </View>
        <View style={styles.stat}>
          <Text style={[styles.statValue, { color: theme.colors.onSurface }]}>{formatCents(stats.bestDayCents)}</Text>
          <Text style={[styles.statLabel, { color: theme.colors.onSurfaceVariant }]}>Best day</Text>
        </View>
        <View style={styles.stat}>
          <Text style={[styles.statValue, { color: theme.colors.onSurface }]}>{formatCents(stats.averageDailyCents)}</Text>
          <Text style={[styles.statLabel, { color: theme.colors.onSurfaceVariant }]}>Average daily</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: radius.lg, padding: spacing.lg, gap: spacing.xs },
  label: { ...typography.bodySmall },
  total: { ...typography.display },
  grid: { flexDirection: "row", justifyContent: "space-between", borderTopWidth: StyleSheet.hairlineWidth, marginTop: spacing.md, paddingTop: spacing.md },
  stat: { gap: 2, alignItems: "flex-start" },
  statValue: { ...typography.h2, fontWeight: "700" },
  statLabel: { ...typography.caption },
});
