import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  percent: number;
}

/** Small, quiet progress indicator — one line of text, one thin bar.
 *  Not a badge, not a celebratory animation: "the goal is completion,
 *  not gamification" per the spec. */
export function CompletionBar({ percent }: Props) {
  const theme = useTheme();
  const clamped = Math.max(0, Math.min(100, percent));

  return (
    <View style={styles.wrapper}>
      <View style={styles.labelRow}>
        <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Business profile</Text>
        <Text style={[styles.percent, { color: theme.colors.onSurfaceVariant }]}>{clamped}% complete</Text>
      </View>
      <View style={[styles.track, { backgroundColor: theme.colors.surfaceVariant }]}>
        <View style={[styles.fill, { width: `${clamped}%`, backgroundColor: theme.colors.primary }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: spacing.xs },
  labelRow: { flexDirection: "row", justifyContent: "space-between" },
  label: { ...typography.bodySmall },
  percent: { ...typography.bodySmall, fontWeight: "600" },
  track: { height: 6, borderRadius: radius.pill, overflow: "hidden" },
  fill: { height: "100%", borderRadius: radius.pill },
});
