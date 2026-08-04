/**
 * InsightList — factual behavioural statements about a customer.
 * ONLY renders BehaviouralInsight values — see riskIndicator.ts.
 *
 * RAW ROWS, NO CARD. No background, no border, no radius — plain text
 * lines with a colour dot, matching the flat-row treatment applied
 * across every list in this feature (see the same reasoning in
 * CustomerCard/LoanCard/RestoreRow: a card per item is real rendering
 * and vertical-space cost that only shows up once a real user has real
 * volume — an insight list has no reason to be an exception).
 *
 * DOT LOGIC: POSITIVE gets a green dot, ATTENTION gets a red dot.
 * NEUTRAL gets NO dot at all — a grey dot next to a fact that's neither
 * good nor bad news doesn't communicate anything a plain line doesn't
 * already say, and an empty slot keeps the row's leading edge aligned
 * with the ones that do have a dot.
 */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { BehaviouralInsight } from "../types";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  insights: BehaviouralInsight[];
  title?: string;
}

export function InsightList({ insights, title = "Payment history" }: Props) {
  const theme = useTheme();
  if (insights.length === 0) return null;

  const toneColour = (tone: BehaviouralInsight["tone"]): string | null => {
    switch (tone) {
      case "POSITIVE":
        return theme.colors.secondary;
      case "ATTENTION":
        return theme.colors.error;
      default:
        return null; // NEUTRAL — no dot, see docstring
    }
  };

  return (
    <View style={styles.wrapper}>
      <Text style={[styles.title, { color: theme.colors.onSurface }]}>{title}</Text>
      {insights.map((insight) => {
        const dotColour = toneColour(insight.tone);
        return (
          <View key={insight.kind} style={styles.row}>
            <View style={styles.dotSlot}>
              {dotColour && <View style={[styles.dot, { backgroundColor: dotColour }]} />}
            </View>
            <Text style={[styles.statement, { color: theme.colors.onSurface }]}>{insight.statement}</Text>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: spacing.sm },
  title: { ...typography.h2 },
  row: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  dotSlot: { width: 8, alignItems: "center" },
  dot: { width: 8, height: 8, borderRadius: 4 },
  statement: { ...typography.body, flex: 1 },
});
