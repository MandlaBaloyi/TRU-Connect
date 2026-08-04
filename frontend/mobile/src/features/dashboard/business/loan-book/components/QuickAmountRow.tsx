/**
 * QuickAmountRow — one-tap payment amounts. Theme-aware.
 */

import React from "react";
import { Pressable, ScrollView, StyleSheet, Text } from "react-native";
import { useTheme } from "react-native-paper";

import type { Cents } from "../types";
import { formatCentsCompact } from "../services/loanMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  amounts: Cents[];
  selected?: Cents;
  outstanding: Cents;
  onSelect: (amount: Cents) => void;
}

export function QuickAmountRow({ amounts, selected, outstanding, onSelect }: Props) {
  const theme = useTheme();

  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
      {amounts.map((amount) => {
        const isSelected = selected === amount;
        const isFullSettlement = amount === outstanding;
        return (
          <Pressable
            key={amount}
            onPress={() => onSelect(amount)}
            style={[
              styles.chip,
              { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
              isSelected && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
              isFullSettlement && !isSelected && { borderColor: theme.colors.secondary, borderWidth: 2 },
            ]}
            accessibilityRole="button"
            accessibilityState={{ selected: isSelected }}
            accessibilityLabel={
              isFullSettlement ? `Pay the full ${formatCentsCompact(amount)}` : `Pay ${formatCentsCompact(amount)}`
            }
          >
            <Text
              style={[
                styles.chipText,
                { color: isSelected ? theme.colors.onPrimary : theme.colors.onSurface },
              ]}
            >
              {isFullSettlement ? `All · ${formatCentsCompact(amount)}` : formatCentsCompact(amount)}
            </Text>
          </Pressable>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: { gap: spacing.sm, paddingVertical: spacing.xs },
  chip: {
    minHeight: 48,
    minWidth: 80,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
  },
  chipText: { ...typography.body, fontWeight: "600" },
});
