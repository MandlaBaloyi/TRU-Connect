import React from "react";
import { Pressable, ScrollView, StyleSheet, Text } from "react-native";
import { useTheme } from "react-native-paper";

import type { InventoryFilter } from "../types";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  filter: InventoryFilter;
  onFilterChange: (filter: InventoryFilter) => void;
}

const OPTIONS: { value: InventoryFilter; label: string }[] = [
  { value: "ALL", label: "All" },
  { value: "IN_STOCK", label: "In Stock" },
  { value: "LOW_STOCK", label: "Low Stock" },
  { value: "OUT_OF_STOCK", label: "Out of Stock" },
];

export function InventoryFilterBar({ filter, onFilterChange }: Props) {
  const theme = useTheme();
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
      {OPTIONS.map((option) => {
        const selected = option.value === filter;
        return (
          <Pressable
            key={option.value}
            onPress={() => onFilterChange(option.value)}
            style={[
              styles.chip,
              { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
              selected && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
            ]}
            accessibilityRole="button"
            accessibilityState={{ selected }}
            accessibilityLabel={`Filter: ${option.label}`}
          >
            <Text style={[styles.chipText, { color: selected ? theme.colors.onPrimary : theme.colors.onSurface }]}>
              {option.label}
            </Text>
          </Pressable>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: spacing.xs },
  chip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: radius.pill,
    minHeight: 32,
    justifyContent: "center",
    borderWidth: 1,
  },
  chipText: { ...typography.bodySmall, fontWeight: "600" },
});
