import React from "react";
import { StyleSheet, View } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { CheckCircle2, EyeOff } from "lucide-react-native";

import { useVerificationStatus } from "../hooks/useVerificationStatus";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * "Can businesses see me at all?" -- the supplier's own view of the
 * verification curtain (V2_12 Phase 1).
 *
 * WHY THIS LIVES IN features/.../verification/components AND NOT IN
 * THE SETTINGS FOLDER THAT RENDERS IT. Settings is its first home, not
 * its only one: the same card belongs on the supplier Home tab once
 * Home is built, and a component that lives inside the screen that
 * happens to show it first is a component the second screen copies.
 * Verification owns it; screens borrow it.
 *
 * IT REPLACED A PERSISTENT TOP BANNER, and the reason is worth
 * recording. A strip pinned to every screen was unmissable on day one
 * and furniture by day three -- people stop seeing a banner that never
 * changes -- while costing vertical space during the exact task
 * (building a catalogue) where the screen is most crowded. It also
 * drew under the status bar on an edge-to-edge app, which is how the
 * whole question got asked.
 *
 * ON THIS SCREEN IT IS THE MASTER SWITCH THE SUPPLIER CANNOT FLIP, and
 * that is why it sits at the top rather than at the bottom. Every
 * other control here answers "who can see this?" -- and while
 * verification is pending the honest answer to all of them is NOBODY.
 * Setting a photo to "Everyone" beneath a card saying nobody can see
 * you is a contradiction the supplier should read in that order.
 *
 * RENDERS IN BOTH STATES, unlike the banner it replaced. "Your shop is
 * live" is worth confirming on a screen about visibility; a card that
 * only ever appears when something is wrong teaches people that its
 * absence means nothing in particular.
 */
export function VerificationStatusCard() {
  const theme = useTheme();
  const { data, isLoading } = useVerificationStatus();

  if (isLoading || !data) return null;

  const live = data.visibleToBuyers;
  const accent = live ? theme.colors.secondary : theme.colors.primary;
  const Icon = live ? CheckCircle2 : EyeOff;

  return (
    <View
      style={[
        styles.card,
        { backgroundColor: theme.colors.surface, borderColor: accent },
      ]}
    >
      <View style={styles.header}>
        <Icon size={20} color={accent} strokeWidth={2} />
        <Text style={[styles.headline, { color: theme.colors.onSurface }]}>{data.headline}</Text>
      </View>
      <Text style={[styles.detail, { color: theme.colors.onSurfaceVariant }]}>{data.detail}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderRadius: radius.md,
    padding: spacing.md,
    gap: spacing.xs,
  },
  header: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  headline: { ...typography.body, fontWeight: "600" as const, flex: 1 },
  // bodySmall (13), not caption (11): this is a sentence to read,
  // not a label to glance at.
  detail: { ...typography.bodySmall },
});
