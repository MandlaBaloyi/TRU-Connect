import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { MD3Theme, useTheme } from "react-native-paper";

import type { InventoryStatus } from "../types";
import { palette } from "@/theme/colors";
import { typography } from "@/theme/typography";

interface StatusStyle {
  label: string;
  fg: string;
}

function resolve(status: InventoryStatus, theme: MD3Theme): StatusStyle {
  switch (status) {
    case "IN_STOCK":
      return { label: "In stock", fg: palette.success };
    case "LOW_STOCK":
      return { label: "Low stock", fg: palette.warning };
    case "OUT_OF_STOCK":
      return { label: "Out of stock", fg: theme.colors.error };
    default:
      return { label: String(status), fg: theme.colors.onSurfaceVariant };
  }
}

interface Props {
  status: InventoryStatus;
}

export function InventoryStatusBadge({ status }: Props) {
  const theme = useTheme();
  const style = resolve(status, theme);
  return (
    <View style={styles.row} accessibilityRole="text" accessibilityLabel={style.label}>
      <Text style={[styles.symbol, { color: style.fg }]}>●</Text>
      <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
        {style.label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: 4 },
  symbol: { fontSize: 10 },
  label: { ...typography.bodySmall },
});
