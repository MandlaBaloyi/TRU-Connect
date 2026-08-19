/**
 * ProductStatusFilterBar — four options now, not three: All/In stock/
 * Out of stock/Archived, per review ("Archived is primarily for
 * recovery/management... on the Products screen, your filter could
 * eventually be [All][In stock][Out of stock][Archived]"). Filters on
 * ProductListFilter, NOT StockStatus -- Archived is a lifecycle
 * concern layered on top of, not a fourth stock state (see types.ts's
 * own docstring on why those stay separate unions).
 *
 * Same visual language as every other filter bar in this app (Order
 * Book's OrderStatusFilterBar, Loan Book's CustomerFilterBar) -- one
 * consistent chip style for this kind of control, not a new one here.
 */

import React from "react";
import { Pressable, ScrollView, StyleSheet, Text } from "react-native";
import { useTheme } from "react-native-paper";
import { Archive } from "lucide-react-native";

import type { ProductListFilter } from "../types";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  filter: ProductListFilter;
  onFilterChange: (filter: ProductListFilter) => void;
}

const OPTIONS: { value: ProductListFilter; label: string }[] = [
  { value: "ALL", label: "All" },
  { value: "IN_STOCK", label: "In stock" },
  { value: "OUT_OF_STOCK", label: "Out of stock" },
  { value: "ARCHIVED", label: "Archived" },
];

export function ProductStatusFilterBar({ filter, onFilterChange }: Props) {
  const theme = useTheme();
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      // SINGLE ROW, NEVER WRAPPED -- flexWrap previously let "Out of
      // stock" (the longest label) push chips onto a second, uneven
      // line on narrower screens, which broke the equal-gap look even
      // though `gap` itself was always consistent. A scrollable single
      // row keeps the spacing genuinely uniform on every screen width,
      // matching the reviewed request directly instead of only
      // technically satisfying it.
      contentContainerStyle={styles.row}
    >
      {OPTIONS.map((option) => {
        const selected = option.value === filter;
        const color = selected ? theme.colors.onPrimary : theme.colors.onSurface;
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
            {option.value === "ARCHIVED" && <Archive size={13} color={color} strokeWidth={2} />}
            <Text style={[styles.chipText, { color }]}>{option.label}</Text>
          </Pressable>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: spacing.xs },
  chip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: radius.pill,
    minHeight: 32,
    justifyContent: "center",
    borderWidth: 1,
  },
  chipText: { ...typography.bodySmall, fontWeight: "600" },
});
