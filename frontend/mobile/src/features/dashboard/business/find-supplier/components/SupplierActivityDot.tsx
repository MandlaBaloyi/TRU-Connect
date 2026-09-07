import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { SupplierActivity } from "../types";

/**
 * "Active now" / "Active 20 minutes ago", with a green dot when the
 * supplier is genuinely online.
 *
 * WHY THIS EARNS A SPOT IN THE BRAND HEADER: a business about to place
 * an order is really asking "will anyone see this today". That's a fact
 * about the supplier, exactly like their name and how long they've been
 * on TruConnect, and it shouldn't take a scroll to find. It also makes
 * the difference between an order that's confirmed in ten minutes and
 * one that sits until a sweeper auto-declines it.
 *
 * RENDERS NOTHING WHEN `activity` IS NULL, which is the normal case:
 * the backend omits the whole object unless the supplier switched
 * sharing on (SupplierProfile.show_last_active). The absence IS the
 * gate — there's no flag to forget to check here.
 *
 * `isOnline` comes from the SERVER, not from comparing the timestamp
 * here, so this screen, the connections list and anything added later
 * all agree on what "online" means.
 */
export function SupplierActivityDot({ activity }: { activity: SupplierActivity | null }) {
  const theme = useTheme();
  if (!activity) return null;

  const colour = activity.isOnline ? theme.colors.secondary : theme.colors.onSurfaceVariant;

  return (
    <View style={styles.row}>
      <View style={[styles.dot, { backgroundColor: colour }]} />
      <Text style={[styles.text, { color: colour }]}>{formatActivity(activity)}</Text>
    </View>
  );
}

/**
 * PRECISE, on purpose. Granularity follows the unit — minutes up to an
 * hour, whole hours up to a day, then days. A business deciding who to
 * order from today needs "5 minutes ago" and "just now" to be different
 * answers; past an hour the exact minute stops changing the decision.
 *
 * The supplier's own on/off switch is the privacy control, so there's
 * nothing to gain by blurring the number once they've opted in.
 */
export function formatActivity(activity: SupplierActivity): string {
  if (activity.isOnline) return "Active now";

  const minutes = Math.floor((Date.now() - new Date(activity.lastActiveAt).getTime()) / 60_000);
  if (minutes < 60) {
    const safe = Math.max(minutes, 1);
    return `Active ${safe} ${safe === 1 ? "minute" : "minutes"} ago`;
  }

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `Active ${hours} ${hours === 1 ? "hour" : "hours"} ago`;

  const days = Math.floor(hours / 24);
  if (days === 1) return "Active yesterday";
  if (days < 7) return `Active ${days} days ago`;

  const weeks = Math.floor(days / 7);
  if (weeks < 5) return `Active ${weeks} ${weeks === 1 ? "week" : "weeks"} ago`;

  const months = Math.floor(days / 30);
  return `Active ${months} ${months === 1 ? "month" : "months"} ago`;
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: spacing.xs,
    paddingHorizontal: spacing.md,
  },
  dot: { width: 8, height: 8, borderRadius: 4 },
  text: { ...typography.bodySmall, fontWeight: "600" },
});
