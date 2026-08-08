import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Check } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Option<T extends string> {
  value: T;
  label: string;
}

interface Props<T extends string> {
  label: string;
  options: Option<T>[];
  value: T[];
  onChange: (value: T[]) => void;
}

/** Checkbox-style multiple choice, rendered as chips. Toggling adds/
 *  removes from the array — no "select all" trap, no minimum count
 *  enforced here (a screen can validate "at least one" itself if that
 *  field is required). */
export function ChipMultiSelect<T extends string>({ label, options, value, onChange }: Props<T>) {
  const theme = useTheme();

  const toggle = (option: T) => {
    if (value.includes(option)) {
      onChange(value.filter((v) => v !== option));
    } else {
      onChange([...value, option]);
    }
  };

  return (
    <View style={styles.wrapper}>
      <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>{label}</Text>
      <View style={styles.row}>
        {options.map((option) => {
          const selected = value.includes(option.value);
          return (
            <Pressable
              key={option.value}
              onPress={() => toggle(option.value)}
              style={[
                styles.chip,
                { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
                selected && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
              ]}
              accessibilityRole="checkbox"
              accessibilityState={{ checked: selected }}
              accessibilityLabel={option.label}
            >
              {selected && <Check size={13} color={theme.colors.onPrimary} strokeWidth={3} />}
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
  chip: {
    flexDirection: "row", alignItems: "center", gap: 4,
    paddingHorizontal: spacing.md, paddingVertical: spacing.xs,
    borderRadius: radius.pill, minHeight: 36, justifyContent: "center", borderWidth: 1,
  },
  chipText: { ...typography.bodySmall, fontWeight: "600" },
});
