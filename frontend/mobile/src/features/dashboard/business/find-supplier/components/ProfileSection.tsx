import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * One labelled block of the supplier profile — "Supplier details",
 * "Track record", "Delivery & collection", "Products".
 *
 * WHAT THIS REPLACED, and why: the first attempt separated sections
 * with full-bleed tinted bands. On a real device those read as stray
 * lavender stripes rather than structure — the theme's surfaceVariant
 * is a tint meant for small chips and icon wells, and stretched
 * edge-to-edge it looked like a rendering artefact, not a deliberate
 * gutter. Reported directly.
 *
 * The replacement does the job with a NAME instead of a colour: a
 * small muted caption tells you what the block is, which separates it
 * far better than any divider and answers "what am I looking at" at
 * the same time. Whitespace does the rest. Nothing tinted, nothing
 * full-bleed, and one less colour on a screen that already carries
 * product photography.
 */
export function ProfileSection({
  label,
  children,
  /** Rendered on the label row, right of the title — an InfoHint, in
   *  practice. */
  accessory,
}: {
  label?: string;
  children: React.ReactNode;
  accessory?: React.ReactNode;
}) {
  const theme = useTheme();

  return (
    <View style={styles.section}>
      {label && (
        <View style={styles.labelRow}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>{label}</Text>
          {accessory}
        </View>
      )}
      {children}
    </View>
  );
}

/** The shared card the profile's blocks sit in — one border radius,
 *  one border colour, one padding, so "Supplier details" and "Track
 *  record" are visibly the same kind of object. */
export function ProfileCard({ children }: { children: React.ReactNode }) {
  const theme = useTheme();
  return (
    <View
      style={[styles.card, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  section: { paddingHorizontal: spacing.md, paddingTop: spacing.lg, gap: spacing.sm },
  labelRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  label: {
    ...typography.bodySmall,
    fontWeight: "700",
    fontSize: 12,
    textTransform: "uppercase",
    letterSpacing: 0.6,
  },
  card: { borderRadius: 14, borderWidth: 1, overflow: "hidden" },
});
