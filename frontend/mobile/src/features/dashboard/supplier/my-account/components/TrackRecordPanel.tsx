import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { InfoHint } from "@/components/ui/InfoHint";
import { formatCents } from "../../products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { SupplierPerformance } from "../services/accountService";

/**
 * The supplier's OWN track record — deliberately a different set of
 * figures from the one businesses see on their brand profile.
 *
 * WHY TWO SETS AND NOT ONE PANEL WITH A SWITCH. The two audiences need
 * opposite things from the same order rows:
 *
 *   A BUSINESS needs signals that are hard to fake and fair to a
 *   newcomer — so their view is counts that only grow and vanish at
 *   zero. Nothing there can make a supplier look bad.
 *
 *   A SUPPLIER needs signals that say what to FIX. Acceptance rate,
 *   reply time and cancellations are exactly that — and exactly what
 *   was removed from the public profile, because publicly they punish
 *   one bad week ("accepted 0 of 1") while privately they're the most
 *   actionable numbers a supplier has.
 *
 * ALWAYS VISIBLE TO THE SUPPLIER, even with the businesses-facing
 * toggle off: that switch controls who ELSE sees the public figures,
 * never whether a supplier can see their own.
 *
 * THIS IS THE SEED OF THE ANALYTICS SCREEN. It lives on the profile
 * only because no analytics section exists yet; when one does, this
 * panel is what moves into it.
 */
export function TrackRecordPanel({ performance }: { performance: SupplierPerformance | null | undefined }) {
  const theme = useTheme();

  // No orders decided yet -> nothing honest to report. A grid of
  // zeroes would read as failure to a supplier who simply hasn't
  // started.
  if (!performance || (performance.decidedCount === 0 && performance.unitsSoldCount === 0)) {
    return (
      <View style={[styles.empty, { backgroundColor: theme.colors.surfaceVariant }]}>
        <Text style={[styles.emptyText, { color: theme.colors.onSurfaceVariant }]}>
          Your track record appears here once businesses start ordering from you.
        </Text>
      </View>
    );
  }

  const acceptanceLabel =
    performance.decidedCount > 0
      ? `${performance.acceptedCount} of ${performance.decidedCount}`
      : "—";

  return (
    <View style={styles.grid}>
      <Stat
        value={formatCents(performance.totalSalesCents)}
        label="total sales"
        hint="Everything you've sold through accepted orders on TruConnect. Businesses never see this figure — it's yours."
      />
      <Stat
        value={performance.unitsSoldCount.toLocaleString()}
        label="units sold"
        hint="Total items sold across all accepted orders. Businesses don't see this — your public record shows how many orders you accepted, not the volume inside them."
      />

      <Stat
        value={performance.repeatBusinessCount.toLocaleString()}
        label="businesses ordered again"
        hint="Businesses that came back for a second order. This is the clearest read you have on whether the first order went well — nothing else here is as hard to fake. It used to be on your public profile and was moved here: it says how you're performing, which is yours to act on, rather than where you stand, which is what strangers are reading."
      />
      <Stat
        value={acceptanceLabel}
        label="recent orders accepted"
        hint="Of your most recent decided orders, how many you accepted. Businesses do NOT see this — a rate is unfair to judge a supplier on publicly, but it's the clearest signal you have about whether you're turning work away."
      />
      <Stat
        value={formatResponse(performance.medianResponseHours)}
        label="typical reply time"
        hint="How long you usually take to accept or decline. Businesses don't see it — but they feel it: an order that sits unanswered is one they'll place with someone else next time."
      />
      <Stat
        value={String(performance.ordersThisMonth)}
        label="orders this month"
        hint="Accepted orders in the last 30 days, so you can see a slowdown while it's happening rather than months later."
      />
      <Stat
        value={String(performance.cancelledAfterConfirming)}
        label="cancelled after accepting"
        tone={performance.cancelledAfterConfirming > 0 ? "warn" : undefined}
        hint="Orders you accepted and then cancelled. Only your own cancellations count — a business changing their mind isn't your record. Businesses don't see this number, but they do remember the experience."
      />
    </View>
  );
}

function Stat({
  value,
  label,
  hint,
  tone,
}: {
  value: string;
  label: string;
  hint: string;
  tone?: "warn";
}) {
  const theme = useTheme();
  return (
    <View style={[styles.stat, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
      <View style={styles.statTop}>
        <Text
          style={[
            styles.value,
            { color: tone === "warn" ? theme.colors.error : theme.colors.onSurface },
          ]}
          numberOfLines={1}
          adjustsFontSizeToFit
        >
          {value}
        </Text>
        <InfoHint title={label} body={hint} size={14} />
      </View>
      <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>{label}</Text>
    </View>
  );
}

/** Rounded the way a person would say it. */
function formatResponse(hours: number | null): string {
  if (hours === null) return "—";
  if (hours < 1) return "< 1 hr";
  if (hours < 24) return `${Math.round(hours)} hr`;
  const days = Math.round(hours / 24);
  return `${days} ${days === 1 ? "day" : "days"}`;
}

const styles = StyleSheet.create({
  grid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  // Two per row on a phone: these are glanceable figures, and a single
  // column would push six of them past a screen.
  stat: {
    width: "48%",
    flexGrow: 1,
    padding: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
    gap: 2,
  },
  statTop: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: spacing.xs },
  value: { ...typography.h2, fontWeight: "800", flexShrink: 1 },
  label: { ...typography.bodySmall, fontSize: 12 },
  empty: { padding: spacing.md, borderRadius: radius.lg },
  emptyText: { ...typography.bodySmall, lineHeight: 19 },
});
