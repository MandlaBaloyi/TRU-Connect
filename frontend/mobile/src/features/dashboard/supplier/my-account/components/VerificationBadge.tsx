/**
 * Verification badge — a TRUST indicator, not a social-media blue
 * tick (file.txt §18). Icon + text + colour together, never colour
 * alone (§19 accessibility).
 *
 * SIMPLIFIED to one state, not five — see types.ts's own
 * TrustVerificationStatus docstring for the full reasoning. The
 * previous version mapped five UI states off email-OTP confirmation,
 * which was the actual bug: it let "Verified" mean "confirmed an
 * inbox," not a real identity/business check. There is currently
 * nothing behind this concept, so there's nothing honest to say about
 * PENDING/REQUIRED/FAILED yet either — the caller only ever renders
 * this component when trustVerification === "VERIFIED" (see
 * MyAccountScreen.tsx), which right now is never. No status prop
 * needed until there's a real state machine behind it.
 */
import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { BadgeCheck } from "lucide-react-native";

import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

export function VerificationBadge() {
  const theme = useTheme();

  return (
    <View
      style={[styles.pill, { backgroundColor: theme.colors.secondaryContainer }]}
      accessibilityRole="text"
      accessibilityLabel="Verified"
    >
      <BadgeCheck size={14} color={theme.colors.secondary} strokeWidth={2.2} />
      <Text style={[styles.text, { color: theme.colors.secondary }]}>Verified</Text>
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
