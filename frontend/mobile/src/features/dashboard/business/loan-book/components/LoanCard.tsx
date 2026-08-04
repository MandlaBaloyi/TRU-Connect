/**
 * LoanCard — one credit-sale entry in a list. Theme-aware.
 */

import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { LoanEntryView } from "../types";
import { formatCents } from "../services/loanMapper";
import { formatAge } from "../algorithms/agingCalculator";
import { describeOverdueFact } from "../algorithms/riskIndicator";
import { CustomerAvatar } from "./CustomerAvatar";
import { LoanStatusBadge } from "./LoanStatusBadge";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  view: LoanEntryView;
  customerName: string;
  onPress?: () => void;
}

export function LoanCard({ view, customerName, onPress }: Props) {
  const theme = useTheme();
  const overdueFact = describeOverdueFact(view.entry, view.payments);
  const isPartlyPaid = view.amountPaid > 0 && view.outstandingAmount > 0;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
      accessibilityRole="button"
      accessibilityLabel={`${customerName}, ${formatCents(view.outstandingAmount)} owed`}
    >
      <CustomerAvatar name={customerName} seed={view.entry.customerId} />

      <View style={styles.body}>
        <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={1}>
          {customerName}
        </Text>
        <Text style={[styles.meta, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
          {view.entry.description ? `${view.entry.description} · ` : ""}
          {formatAge(view.ageInDays)}
        </Text>
        {isPartlyPaid && (
          <Text style={[styles.partial, { color: theme.colors.onSurfaceVariant }]}>
            {formatCents(view.amountPaid)} of {formatCents(view.entry.originalAmount)} paid
          </Text>
        )}
        <LoanStatusBadge status={view.status} detail={overdueFact ?? undefined} />
      </View>

      <View style={styles.amountColumn}>
        <Text
          style={[
            styles.amount,
            { color: theme.colors.onSurface },
            view.status === "PAID" && { color: theme.colors.onSurfaceVariant, fontWeight: "400" },
            view.status === "OVERDUE" && { color: theme.colors.error },
          ]}
          numberOfLines={1}
        >
          {formatCents(view.outstandingAmount)}
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: spacing.md,
    paddingVertical: spacing.sm,
  },
  pressed: { opacity: 0.7 },
  body: { flex: 1, gap: spacing.xs },
  name: { ...typography.h2 },
  meta: { ...typography.bodySmall },
  partial: { ...typography.caption },
  amountColumn: { alignItems: "flex-end" },
  amount: { ...typography.h2, fontWeight: "700" },
});
