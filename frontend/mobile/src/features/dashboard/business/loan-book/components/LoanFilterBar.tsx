/**
 * LoanFilterBar — status chips plus a sort selector. Theme-aware.
 */

import React from "react";
import { Pressable, ScrollView, StyleSheet, Text } from "react-native";
import { useTheme } from "react-native-paper";

import type { LoanSortOption, LoanStatus } from "../types";
import { SORT_LABELS, STATUS_LABELS } from "../services/loanFilters";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

const STATUS_OPTIONS: (LoanStatus | undefined)[] = [undefined, "OUTSTANDING", "OVERDUE", "PAID"];
const SORT_OPTIONS: LoanSortOption[] = ["NEWEST", "OLDEST", "HIGHEST_AMOUNT", "MOST_OVERDUE"];

interface Props {
  status?: LoanStatus;
  onStatusChange: (status?: LoanStatus) => void;
  sortBy: LoanSortOption;
  onSortChange: (sort: LoanSortOption) => void;
}

export function LoanFilterBar({ status, onStatusChange, sortBy, onSortChange }: Props) {
  const theme = useTheme();

  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
      {STATUS_OPTIONS.map((option) => {
        const selected = status === option;
        const label = option ? STATUS_LABELS[option] : "All";
        return (
          <Pressable
            key={label}
            onPress={() => onStatusChange(option)}
            style={[
              styles.chip,
              { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
              selected && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
            ]}
            accessibilityRole="button"
            accessibilityState={{ selected }}
            accessibilityLabel={`Show ${label}`}
          >
            <Text style={[styles.chipText, { color: selected ? theme.colors.onPrimary : theme.colors.onSurface }]}>
              {label}
            </Text>
          </Pressable>
        );
      })}

      <Pressable
        onPress={() => {
          const index = SORT_OPTIONS.indexOf(sortBy);
          onSortChange(SORT_OPTIONS[(index + 1) % SORT_OPTIONS.length]);
        }}
        style={[
          styles.chip,
          styles.sortChip,
          { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
        ]}
        accessibilityRole="button"
        accessibilityLabel={`Sorted by ${SORT_LABELS[sortBy]}. Tap to change.`}
      >
        <Text style={[styles.chipText, { color: theme.colors.onSurface }]}>↕ {SORT_LABELS[sortBy]}</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: { gap: spacing.sm, paddingVertical: spacing.xs },
  chip: {
    minHeight: 36,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
    borderWidth: 1,
  },
  sortChip: { borderStyle: "dashed" },
  chipText: { ...typography.bodySmall },
});
