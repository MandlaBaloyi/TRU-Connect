/**
 * TodayBalanceCard — "how am I doing today", the first thing on the
 * Balances screen. Eye toggle uses the SAME fixed-length mask rule as
 * Loan Book's OutstandingAmountCard (see that file's docstring for why
 * a dot-per-digit mask would still leak magnitude) — session-only,
 * always starts visible on screen open.
 */

import React, { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Eye, EyeOff } from "lucide-react-native";

import { formatCents } from "../services/orderMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

const MASKED_AMOUNT = "R • • • • •";

interface Props {
  totalCents: number;
  completedCount: number;
}

export function TodayBalanceCard({ totalCents, completedCount }: Props) {
  const theme = useTheme();
  const [isHidden, setIsHidden] = useState(false);

  const countLabel = completedCount === 1 ? "1 completed order" : `${completedCount} completed orders`;

  return (
    <View style={[styles.card, { backgroundColor: theme.colors.surface }]}>
      <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>TODAY</Text>
      <View style={styles.amountRow}>
        <Text
          style={[styles.amount, { color: theme.colors.onSurface }]}
          accessibilityRole="text"
          accessibilityLabel={isHidden ? "Amount hidden" : formatCents(totalCents)}
        >
          {isHidden ? MASKED_AMOUNT : formatCents(totalCents)}
        </Text>
        <Pressable
          onPress={() => setIsHidden((prev) => !prev)}
          hitSlop={10}
          style={styles.eyeButton}
          accessibilityRole="button"
          accessibilityLabel={isHidden ? "Show amount" : "Hide amount"}
        >
          {isHidden ? (
            <EyeOff size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
          ) : (
            <Eye size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
          )}
        </Pressable>
      </View>
      <Text style={[styles.meta, { color: theme.colors.onSurfaceVariant }]}>{countLabel}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: radius.lg, padding: spacing.lg, gap: spacing.xs },
  label: { ...typography.bodySmall, fontWeight: "700", letterSpacing: 0.5 },
  amountRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  amount: { ...typography.display },
  eyeButton: { padding: spacing.xs },
  meta: { ...typography.bodySmall },
});
