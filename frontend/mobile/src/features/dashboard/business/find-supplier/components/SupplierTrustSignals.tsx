import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { CircleCheck, Clock, Users } from "lucide-react-native";

import { InfoHint } from "@/components/ui/InfoHint";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { SupplierReliability } from "../types";

/**
 * The three things an informal business actually weighs before sending
 * money to a supplier it has never traded with: do OTHER businesses buy
 * here, do orders go through, and how fast do they answer.
 *
 * EVERY NUMBER HERE IS DERIVED, NOT DECLARED. Connections, acceptance
 * rate and response time all come from what has genuinely happened on
 * the platform — a supplier cannot type any of them in, and there is
 * nothing to game the way a review score invites. That's the whole
 * reason these carry weight where the supplier's own description
 * doesn't.
 *
 * SILENCE IS THE HONEST ANSWER FOR A NEW SUPPLIER. `reliability` is
 * null until there's a real sample (backend:
 * MIN_DECIDED_ORDERS_FOR_RELIABILITY), and a zero connection count
 * renders nothing rather than "0 businesses buy from them" — which
 * would read as a warning about a supplier whose only crime is being
 * new. A supplier with no history simply shows fewer signals; they are
 * never shown a bad one they didn't earn.
 */
export function SupplierTrustSignals({
  connectedBusinessCount,
  reliability,
}: {
  connectedBusinessCount: number;
  reliability: SupplierReliability | null;
}) {
  const theme = useTheme();

  const signals: { icon: React.ReactNode; text: string; hint: string }[] = [];

  if (connectedBusinessCount > 0) {
    signals.push({
      icon: <Users size={15} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />,
      text: `${connectedBusinessCount} ${connectedBusinessCount === 1 ? "business buys" : "businesses buy"} from them`,
      hint: "How many businesses are currently connected to this supplier on TruConnect. It counts real, active connections — not followers or views.",
    });
  }

  if (reliability) {
    const { decidedCount, acceptedCount, medianResponseHours } = reliability;
    signals.push({
      icon: <CircleCheck size={15} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />,
      text: `Accepted ${acceptedCount} of their last ${decidedCount} orders`,
      hint: "Orders this supplier accepted rather than declined. Orders still waiting for a decision, and orders the business cancelled themselves, aren't counted either way.",
    });

    if (medianResponseHours !== null) {
      signals.push({
        icon: <Clock size={15} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />,
        text: `Usually replies ${formatResponseTime(medianResponseHours)}`,
        hint: "How long this supplier typically takes to accept or decline an order. It's a typical time, not a promise — one unusually slow week doesn't change it.",
      });
    }
  }

  if (signals.length === 0) return null;

  return (
    <View style={styles.wrap}>
      {signals.map((signal) => (
        <View
          key={signal.text}
          style={[styles.chip, { backgroundColor: theme.colors.surfaceVariant }]}
        >
          {signal.icon}
          <Text style={[styles.text, { color: theme.colors.onSurfaceVariant }]}>{signal.text}</Text>
          <InfoHint title={signal.text} body={signal.hint} size={13} />
        </View>
      ))}
    </View>
  );
}

/** Rounded to something a person would actually say. "Usually replies
 *  in 4.7 hours" is precision nobody asked for and can't act on. */
function formatResponseTime(hours: number): string {
  if (hours < 1) return "within the hour";
  if (hours < 24) {
    const rounded = Math.round(hours);
    return `in about ${rounded} ${rounded === 1 ? "hour" : "hours"}`;
  }
  const days = Math.round(hours / 24);
  return days === 1 ? "within a day" : `in about ${days} days`;
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.xs, paddingHorizontal: spacing.md, alignItems: "center" },
  chip: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    paddingHorizontal: spacing.sm,
    paddingVertical: 5,
    borderRadius: radius.pill,
  },
  text: { ...typography.bodySmall, fontWeight: "600" },
});
