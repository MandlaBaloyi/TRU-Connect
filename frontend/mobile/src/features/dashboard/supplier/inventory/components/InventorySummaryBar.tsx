import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { InventorySummary } from "../types";
import { palette } from "@/theme/colors";
import { typography } from "@/theme/typography";

interface Props {
  summary: InventorySummary;
}

function Stat({ value, label, color }: { value: number; label: string; color: string }) {
  return (
    <View style={styles.stat}>
      <Text style={[styles.statValue, { color }]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

/** Useful numbers, deliberately NOT a dashboard -- per the design
 *  notes' own instruction: four counts, nothing more, no charts. */
export function InventorySummaryBar({ summary }: Props) {
  const theme = useTheme();
  return (
    <View style={styles.row}>
      <Stat value={summary.totalProducts} label="Products" color={theme.colors.onSurface} />
      <Stat value={summary.inStockCount} label="In Stock" color={palette.success} />
      <Stat value={summary.lowStockCount} label="Low Stock" color={palette.warning} />
      <Stat value={summary.outOfStockCount} label="Out of Stock" color={theme.colors.error} />
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", justifyContent: "space-between" },
  stat: { alignItems: "center", gap: 2 },
  statValue: { ...typography.h2, fontWeight: "800" },
  statLabel: { ...typography.caption },
});
