import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * What a business would see under "Last active", shown to the supplier
 * themselves so the setting isn't abstract — they can read the exact
 * words their customers would read before deciding whether to share it.
 *
 * ALWAYS VISIBLE TO THE SUPPLIER, even with the toggle off. Their own
 * activity is not a secret from them; the toggle controls who ELSE sees
 * it. With it off, the row says so plainly rather than hiding, so the
 * setting's effect is legible from the screen alone.
 *
 * The heartbeat behind this is throttled to 5 minutes
 * (core/decorators.LAST_ACTIVE_THROTTLE_MINUTES), so a reading is
 * accurate to within about that -- which is why "Active now" covers
 * the first two minutes rather than claiming second-level precision
 * the data doesn't have.
 */
export function LastActiveRow({
  lastActiveAt,
  isShared,
}: {
  lastActiveAt: string | null | undefined;
  isShared: boolean;
}) {
  const theme = useTheme();
  const label = formatLastActive(lastActiveAt);

  return (
    <View style={styles.row}>
      <View style={[styles.dot, { backgroundColor: isOnline(lastActiveAt) ? theme.colors.secondary : theme.colors.outline }]} />
      <Text style={[styles.text, { color: theme.colors.onSurfaceVariant }]}>
        {isShared ? `Businesses see: ${label}` : `${label} — not shown to businesses`}
      </Text>
    </View>
  );
}

/** "Active now" is a genuinely live window, not a rounding bucket --
 *  anything older reports its real age. See formatLastActive. */
const ONLINE_WITHIN_MINUTES = 2;

function isOnline(iso: string | null | undefined): boolean {
  if (!iso) return false;
  return Date.now() - new Date(iso).getTime() < ONLINE_WITHIN_MINUTES * 60_000;
}

/**
 * PRECISE, on purpose. An earlier version rounded everything under ten
 * minutes to "Active now" on the grounds that finer detail tracked a
 * person more closely than the feature needed. That was the wrong
 * trade for THIS app: a business about to place an order is asking
 * "will someone actually see this in the next few minutes", and
 * "5 minutes ago" and "just now" are different answers to that
 * question. The privacy control is the supplier's own on/off switch
 * (show_last_active) -- once they've chosen to show it, blurring the
 * number helps nobody.
 *
 * Granularity follows the unit: minutes up to an hour, whole hours up
 * to a day, then days. A supplier active 90 minutes ago reads "1 hour
 * ago", not "90 minutes ago" -- past an hour the exact minute stops
 * changing the decision.
 */
export function formatLastActive(iso: string | null | undefined): string {
  if (!iso) return "No activity yet";

  const minutes = Math.floor((Date.now() - new Date(iso).getTime()) / 60_000);
  if (minutes < ONLINE_WITHIN_MINUTES) return "Active now";
  if (minutes < 60) return `Active ${minutes} ${minutes === 1 ? "minute" : "minutes"} ago`;

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
  row: { flexDirection: "row", alignItems: "center", gap: spacing.xs, marginTop: spacing.xs },
  dot: { width: 8, height: 8, borderRadius: 4 },
  text: { ...typography.bodySmall },
});
