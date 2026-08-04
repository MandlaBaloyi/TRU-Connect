/**
 * HistoryEventRow — one line in the Loan Book activity timeline.
 */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { LoanHistoryEvent } from "../types";
import { describeHistoryEvent, historyEventAmountLabel, isNegativeEvent, isRestorativeEvent } from "../services/loanHistory";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  event: LoanHistoryEvent;
  /** Shown when the timeline isn't already scoped to one customer. */
  customerName?: string;
}

export function HistoryEventRow({ event, customerName }: Props) {
  const theme = useTheme();
  const amountLabel = historyEventAmountLabel(event);

  const dotColour = isNegativeEvent(event.eventType)
    ? theme.colors.error
    : isRestorativeEvent(event.eventType)
      ? theme.colors.secondary
      : theme.colors.primary;

  const time = new Date(event.occurredAt).toLocaleTimeString("en-ZA", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <View style={styles.row}>
      <View style={[styles.dot, { backgroundColor: dotColour }]} />
      <View style={styles.body}>
        <View style={styles.topLine}>
          <Text style={[styles.description, { color: theme.colors.onSurface }]} numberOfLines={1}>
            {describeHistoryEvent(event)}
            {customerName ? ` · ${customerName}` : ""}
          </Text>
          {amountLabel && (
            <Text style={[styles.amount, { color: theme.colors.onSurface }]}>{amountLabel}</Text>
          )}
        </View>
        <View style={styles.bottomLine}>
          <Text style={[styles.time, { color: theme.colors.onSurfaceVariant }]}>{time}</Text>
          {event.reason && (
            <Text style={[styles.reason, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
              {" "}
              · {event.reason}
            </Text>
          )}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: spacing.sm, paddingVertical: spacing.xs },
  dot: { width: 8, height: 8, borderRadius: 4, marginTop: 6 },
  body: { flex: 1, gap: 2 },
  topLine: { flexDirection: "row", justifyContent: "space-between", gap: spacing.sm },
  description: { ...typography.body, fontWeight: "600", flex: 1 },
  amount: { ...typography.body, fontWeight: "600" },
  bottomLine: { flexDirection: "row" },
  time: { ...typography.caption },
  reason: { ...typography.caption, flexShrink: 1 },
});
