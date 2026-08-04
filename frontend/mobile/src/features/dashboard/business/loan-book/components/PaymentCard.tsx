/**
 * PaymentCard — one repayment in a history list. Theme-aware.
 */

import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { Payment } from "../types";
import { formatCents } from "../services/loanMapper";
import { formatAge, daysSince } from "../algorithms/agingCalculator";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  payment: Payment;
  onLongPress?: () => void;
}

export function PaymentCard({ payment, onLongPress }: Props) {
  const theme = useTheme();
  return (
    <Pressable
      onLongPress={onLongPress}
      style={({ pressed }) => [styles.row, pressed && onLongPress ? styles.pressed : null]}
      accessibilityRole={onLongPress ? "button" : "text"}
      accessibilityLabel={`Paid ${formatCents(payment.amount)}, ${formatAge(daysSince(payment.paidAt))}`}
    >
      <View style={[styles.tick, { backgroundColor: theme.colors.secondaryContainer }]}>
        <Text style={{ color: theme.colors.onSecondaryContainer, fontWeight: "700" }}>✓</Text>
      </View>
      <View style={styles.body}>
        <Text style={[styles.amount, { color: theme.colors.onSurface }]}>
          {formatCents(payment.amount)}
        </Text>
        <Text style={[styles.meta, { color: theme.colors.onSurfaceVariant }]}>
          {formatAge(daysSince(payment.paidAt))}
          {payment.note ? ` · ${payment.note}` : ""}
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: spacing.md, paddingVertical: spacing.sm },
  pressed: { opacity: 0.6 },
  tick: { width: 32, height: 32, borderRadius: 16, alignItems: "center", justifyContent: "center" },
  body: { flex: 1 },
  amount: { ...typography.body, fontWeight: "600" },
  meta: { ...typography.bodySmall },
});
