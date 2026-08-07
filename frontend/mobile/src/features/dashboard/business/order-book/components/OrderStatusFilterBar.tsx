/**
 * OrderStatusFilterBar — a segmented control, not a dropdown. Four
 * options total (All/Pending/Completed/Cancelled), matching the "few
 * types" simplicity call — no sort options, no date filters.
 *
 * COLOURS MATCH LOAN BOOK'S CustomerFilterBar EXACTLY (same
 * surface+outline unselected chip, same primary/onPrimary selected
 * chip) — the two features use the same visual language for the same
 * kind of control, not two different chip styles that happen to sit in
 * similar places.
 */

import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { OrderStatus } from "../types";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  status: OrderStatus | undefined;
  onStatusChange: (status: OrderStatus | undefined) => void;
}

const OPTIONS: { value: OrderStatus | undefined; label: string }[] = [
  { value: undefined, label: "All" },
  { value: "PENDING", label: "Pending" },
  { value: "COMPLETED", label: "Completed" },
  { value: "CANCELLED", label: "Cancelled" },
];

export function OrderStatusFilterBar({ status, onStatusChange }: Props) {
  const theme = useTheme();
  return (
    <View style={styles.row}>
      {OPTIONS.map((option) => {
        const selected = option.value === status;
        return (
          <Pressable
            key={option.label}
            onPress={() => onStatusChange(option.value)}
            style={[
              styles.chip,
              { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
              selected && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
            ]}
            accessibilityRole="button"
            accessibilityState={{ selected }}
            accessibilityLabel={`Filter: ${option.label}`}
          >
            <Text
              style={[styles.chipText, { color: selected ? theme.colors.onPrimary : theme.colors.onSurface }]}
            >
              {option.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
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