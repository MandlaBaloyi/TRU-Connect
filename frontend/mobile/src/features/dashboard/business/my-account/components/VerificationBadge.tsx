/**
 * Verification badge — a TRUST indicator, not a social-media blue
 * tick (file.txt §18). Deliberately: icon + text + colour together,
 * never colour alone (§19 accessibility), and no numeric score
 * anywhere near it.
 */
import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { AlertCircle, BadgeCheck, Clock, ShieldQuestion, XCircle } from "lucide-react-native";

import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import type { VerificationBadgeStatus } from "../types";

const COPY: Record<VerificationBadgeStatus, string> = {
  VERIFIED: "Verified",
  PENDING: "Verification pending",
  REQUIRED: "Verification required",
  FAILED: "Verification failed",
  UNAVAILABLE: "Verification unavailable",
};

export function VerificationBadge({ status }: { status: VerificationBadgeStatus }) {
  const theme = useTheme();

  const { bg, fg, Icon } = {
    VERIFIED: { bg: theme.colors.secondaryContainer, fg: theme.colors.secondary, Icon: BadgeCheck },
    PENDING: { bg: theme.colors.surfaceVariant, fg: theme.colors.onSurfaceVariant, Icon: Clock },
    REQUIRED: { bg: theme.colors.errorContainer, fg: theme.colors.error, Icon: AlertCircle },
    FAILED: { bg: theme.colors.errorContainer, fg: theme.colors.error, Icon: XCircle },
    UNAVAILABLE: { bg: theme.colors.surfaceVariant, fg: theme.colors.onSurfaceVariant, Icon: ShieldQuestion },
  }[status];

  return (
    <View style={[styles.pill, { backgroundColor: bg }]} accessibilityRole="text" accessibilityLabel={COPY[status]}>
      <Icon size={14} color={fg} strokeWidth={2.2} />
      <Text style={[styles.text, { color: fg }]}>{COPY[status]}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  pill: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: radius.pill,
  },
  text: { ...typography.bodySmall, fontWeight: "700" },
});
