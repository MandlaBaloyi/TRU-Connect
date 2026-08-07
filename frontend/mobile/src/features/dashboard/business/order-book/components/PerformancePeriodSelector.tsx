import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { PerformancePeriod } from "../types";
import { PERFORMANCE_PERIOD_LABELS } from "../types";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  period: PerformancePeriod;
  onChange: (period: PerformancePeriod) => void;
}

const OPTIONS: PerformancePeriod[] = ["3D", "7D", "30D", "3M", "1Y"];

export function PerformancePeriodSelector({ period, onChange }: Props) {
  const theme = useTheme();
  return (
    <View style={styles.row}>
      {OPTIONS.map((option) => {
        const selected = option === period;
        return (
          <Pressable
            key={option}
            onPress={() => onChange(option)}
            style={[styles.chip, { backgroundColor: selected ? theme.colors.primary : theme.colors.surfaceVariant }]}
            accessibilityRole="button"
            accessibilityState={{ selected }}
            accessibilityLabel={PERFORMANCE_PERIOD_LABELS[option]}
          >
            <Text style={[styles.chipText, { color: selected ? theme.colors.onPrimary : theme.colors.onSurfaceVariant }]}>
              {option}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: spacing.xs },
  chip: { flex: 1, alignItems: "center", paddingVertical: spacing.sm, borderRadius: radius.pill, minHeight: 40, justifyContent: "center" },
  chipText: { ...typography.bodySmall, fontWeight: "700" },
});
