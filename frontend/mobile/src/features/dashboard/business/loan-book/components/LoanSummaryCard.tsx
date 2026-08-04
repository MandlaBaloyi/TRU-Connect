/**
 * LoanSummaryCard — a small labelled statistic. Theme-aware.
 */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  label: string;
  value: string;
  caption?: string;
  tone?: "DEFAULT" | "POSITIVE" | "ATTENTION";
}

export function LoanSummaryCard({ label, value, caption, tone = "DEFAULT" }: Props) {
  const theme = useTheme();
  const valueColour =
    tone === "POSITIVE" ? theme.colors.secondary : tone === "ATTENTION" ? theme.colors.error : theme.colors.onSurface;

  return (
    <View style={[styles.card, { backgroundColor: theme.colors.surfaceVariant }]}>
      <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
        {label}
      </Text>
      <Text style={[styles.value, { color: valueColour }]} numberOfLines={1}>
        {value}
      </Text>
      {caption && (
        <Text style={[styles.caption, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
          {caption}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { flex: 1, minWidth: 140, gap: 2, borderRadius: radius.md, padding: spacing.md },
  label: { ...typography.bodySmall },
  value: { ...typography.h1, fontWeight: "700" },
  caption: { ...typography.caption },
});
