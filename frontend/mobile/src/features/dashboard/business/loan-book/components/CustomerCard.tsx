/**
 * CustomerCard — one customer with their total across all entries. Theme-aware.
 */

import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { CustomerView } from "../types";
import { formatCents } from "../services/loanMapper";
import { CustomerAvatar } from "./CustomerAvatar";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  view: CustomerView;
  onPress?: () => void;
}

export function CustomerCard({ view, onPress }: Props) {
  const theme = useTheme();
  const { customer, totalOutstanding, openEntryCount, hasOverdue } = view;
  const entryLabel = openEntryCount === 1 ? "1 unpaid purchase" : `${openEntryCount} unpaid purchases`;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
      accessibilityRole="button"
      accessibilityLabel={`${customer.name}, owes ${formatCents(totalOutstanding)}`}
    >
      <CustomerAvatar name={customer.name} seed={customer.id} />
      <View style={styles.body}>
        <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={1}>
          {customer.name}
        </Text>
        <Text style={[styles.meta, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
          {openEntryCount > 0 ? entryLabel : "All settled"}
        </Text>
      </View>
      <View style={styles.amountColumn}>
        <Text
          style={[styles.amount, { color: hasOverdue ? theme.colors.error : theme.colors.onSurface }]}
          numberOfLines={1}
        >
          {formatCents(totalOutstanding)}
        </Text>
        {hasOverdue && <Text style={[styles.overdueTag, { color: theme.colors.error }]}>Overdue</Text>}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    paddingVertical: spacing.sm,
    minHeight: 44,
  },
  pressed: { opacity: 0.7 },
  body: { flex: 1, gap: 2 },
  name: { ...typography.h2 },
  meta: { ...typography.bodySmall },
  amountColumn: { alignItems: "flex-end", gap: 2 },
  amount: { ...typography.h2, fontWeight: "700" },
  overdueTag: { ...typography.caption },
});
