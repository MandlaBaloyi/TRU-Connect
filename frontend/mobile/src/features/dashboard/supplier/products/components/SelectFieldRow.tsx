import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { ChevronRight } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  label: string;
  valueLabel: string;
  onPress: () => void;
}

export function SelectFieldRow({ label, valueLabel, onPress }: Props) {
  const theme = useTheme();
  return (
    <View style={styles.field}>
      <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>{label}</Text>
      <Pressable
        onPress={onPress}
        style={[styles.row, { borderColor: theme.colors.outline }]}
        accessibilityRole="button"
        accessibilityLabel={`${label}: ${valueLabel}`}
      >
        <Text style={[styles.value, { color: theme.colors.onSurface }]}>{valueLabel}</Text>
        <ChevronRight size={18} color={theme.colors.onSurfaceVariant} />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  field: { gap: spacing.sm },
  label: { ...typography.bodySmall },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    minHeight: 48,
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
  },
  value: { ...typography.body },
});
