import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Option<T extends string> {
  value: T;
  label: string;
}

interface Props<T extends string> {
  label: string;
  options: Option<T>[];
  value: T | undefined;
  onChange: (value: T) => void;
}

/** Radio-style single choice, rendered as chips — same border/fill
 *  convention as every filter bar already in the app. */
export function ChipSingleSelect<T extends string>({ label, options, value, onChange }: Props<T>) {
  const theme = useTheme();
  return (
    <View style={styles.wrapper}>
      <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>{label}</Text>
      <View style={styles.row}>
        {options.map((option) => {
          const selected = option.value === value;
          return (
            <Pressable
              key={option.value}
              onPress={() => onChange(option.value)}
              style={[
                styles.chip,
                { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
                selected && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
              ]}
              accessibilityRole="radio"
              accessibilityState={{ selected }}
              accessibilityLabel={option.label}
            >
              <Text style={[styles.chipText, { color: selected ? theme.colors.onPrimary : theme.colors.onSurface }]}>
                {option.label}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: spacing.xs },
  label: { ...typography.bodySmall, fontWeight: "600" },
  row: { flexDirection: "row", flexWrap: "wrap", gap: spacing.xs },
  chip: { paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: radius.pill, minHeight: 36, justifyContent: "center", borderWidth: 1 },
  chipText: { ...typography.bodySmall, fontWeight: "600" },
});
