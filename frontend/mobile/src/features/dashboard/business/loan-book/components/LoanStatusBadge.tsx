/**
 * LoanStatusBadge — status as icon + colour + text, never colour alone
 * (Doc 02 §5). Colours come from useTheme() so this follows dark mode
 * automatically, the same way AppCard/FeatureTile already do.
 *
 * WARNING colour has no theme-mapped token (paperTheme.ts does not wire
 * one) — palette.warning is used directly for that one case only,
 * matching the fact that lightColors.warning and darkColors.warning are
 * already the same hex in colors.ts (the design system doesn't
 * differentiate it by mode).
 *
 * THE SWITCH HAS A DEFAULT BRANCH ON PURPOSE — see original docstring
 * reasoning: when PENDING_SYNC is added later, this keeps rendering
 * something sensible without an edit here.
 */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { MD3Theme, useTheme } from "react-native-paper";

import type { LoanStatus } from "../types";
import { palette } from "@/theme/colors";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface StatusStyle {
  label: string;
  symbol: string;
  fg: string;
  bg: string;
}

function resolve(status: LoanStatus | string, theme: MD3Theme): StatusStyle {
  switch (status) {
    case "PAID":
      return { label: "Paid", symbol: "✓", fg: theme.colors.secondary, bg: theme.colors.surfaceVariant };
    case "OVERDUE":
      return { label: "Overdue", symbol: "!", fg: theme.colors.error, bg: theme.colors.errorContainer };
    case "OUTSTANDING":
      return { label: "Unpaid", symbol: "•", fg: palette.warning, bg: theme.colors.surfaceVariant };
    default:
      // Unknown status (e.g. a future PENDING_SYNC) — render neutrally
      // rather than blank.
      return { label: String(status), symbol: "•", fg: theme.colors.onSurfaceVariant, bg: theme.colors.surfaceVariant };
  }
}

interface Props {
  status: LoanStatus;
  detail?: string;
}

export function LoanStatusBadge({ status, detail }: Props) {
  const theme = useTheme();
  const style = resolve(status, theme);
  return (
    <View
      style={[styles.badge, { backgroundColor: style.bg }]}
      accessibilityRole="text"
      accessibilityLabel={detail ? `${style.label}, ${detail}` : style.label}
    >
      <Text style={[styles.symbol, { color: style.fg }]}>{style.symbol}</Text>
      <Text style={[styles.label, { color: style.fg }]} numberOfLines={1}>
        {detail ?? style.label}
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
