/**
 * OrderStatusBadge — status as icon + colour + text, never colour alone
 * (same accessibility rule as LoanStatusBadge). Default branch on
 * purpose: if the lifecycle ever grows beyond the current minimal
 * Pending/Completed/Cancelled set, this renders sensibly without an
 * edit here.
 */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { MD3Theme, useTheme } from "react-native-paper";

import type { OrderStatus } from "../types";
import { palette } from "@/theme/colors";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface StatusStyle {
  label: string;
  symbol: string;
  fg: string;
  bg: string;
}

function resolve(status: OrderStatus | string, theme: MD3Theme): StatusStyle {
  switch (status) {
    case "COMPLETED":
      // Matches Loan Book's "Paid" exactly — same meaning (money
      // resolved), same color.
      return { label: "Completed", symbol: "✓", fg: theme.colors.secondary, bg: theme.colors.surfaceVariant };
    case "CANCELLED":
      return { label: "Cancelled", symbol: "✕", fg: theme.colors.error, bg: theme.colors.errorContainer };
    case "PENDING":
      // Matches Loan Book's "Unpaid" exactly — same meaning (money not
      // yet resolved), same color. Was theme.colors.primary (blue)
      // before, which broke the app-wide "orange = still outstanding"
      // color language Loan Book already established.
      return { label: "Pending", symbol: "•", fg: palette.warning, bg: theme.colors.surfaceVariant };
    default:
      return { label: String(status), symbol: "•", fg: theme.colors.onSurfaceVariant, bg: theme.colors.surfaceVariant };
  }
}

interface Props {
  status: OrderStatus;
}

export function OrderStatusBadge({ status }: Props) {
  const theme = useTheme();
  const style = resolve(status, theme);
  return (
    <View
      style={[styles.badge, { backgroundColor: style.bg }]}
      accessibilityRole="text"
      accessibilityLabel={style.label}
    >
      <Text style={[styles.symbol, { color: style.fg }]}>{style.symbol}</Text>
      <Text style={[styles.label, { color: style.fg }]} numberOfLines={1}>
        {style.label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: radius.pill,
    gap: spacing.xs,
  },
  symbol: { ...typography.caption, fontWeight: "700" },
  label: { ...typography.caption },
});
