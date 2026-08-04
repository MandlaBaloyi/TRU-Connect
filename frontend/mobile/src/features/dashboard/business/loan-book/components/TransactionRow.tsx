/**
 * TransactionRow — one line in Transaction History. Bank-statement
 * style: customer name, transaction type, amount, time.
 *
 * Reuses LoanCard's visual grammar (name+meta stacked left, amount+meta
 * stacked right) rather than inventing a new layout shape — keeps the
 * whole feature's visual language consistent instead of adding a fourth
 * distinct row pattern alongside CustomerCard/LoanCard/RestoreRow.
 *
 * RAW ROW, NO CARD — same flat treatment as every other list in this
 * feature; the parent screen supplies a hairline separator between rows.
 *
 * COLOUR is restrained on purpose: a payment coming in is positive
 * (green), a reversed payment is attention (red), but a loan simply
 * being recorded is neutral — recording a sale isn't good or bad news,
 * so it gets no colour emphasis, matching InsightList's same restraint
 * for its neutral-tone facts.
 */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { LoanHistoryEvent } from "../types";
import { historyEventAmountLabel, transactionTone, transactionTypeLabel } from "../services/loanHistory";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  event: LoanHistoryEvent;
  customerName: string;
}

export function TransactionRow({ event, customerName }: Props) {
  const theme = useTheme();
  const tone = transactionTone(event.eventType);
  const amountLabel = historyEventAmountLabel(event);

  const toneColour =
    tone === "POSITIVE" ? theme.colors.secondary : tone === "ATTENTION" ? theme.colors.error : theme.colors.onSurface;

  const time = new Date(event.occurredAt).toLocaleTimeString("en-ZA", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <View style={styles.row}>
      <View style={styles.left}>
        <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={1}>
          {customerName}
        </Text>
        <Text style={[styles.type, { color: tone === "NEUTRAL" ? theme.colors.onSurfaceVariant : toneColour }]}>
          {transactionTypeLabel(event.eventType)}
        </Text>
      </View>
      <View style={styles.right}>
        {amountLabel && <Text style={[styles.amount, { color: toneColour }]}>{amountLabel}</Text>}
        <Text style={[styles.time, { color: theme.colors.onSurfaceVariant }]}>{time}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: spacing.sm },
  left: { flex: 1, gap: 2, marginRight: spacing.sm },
  name: { ...typography.body, fontWeight: "600" },
  type: { ...typography.caption },
  right: { alignItems: "flex-end", gap: 2 },
  amount: { ...typography.body, fontWeight: "700" },
  time: { ...typography.caption },
});
