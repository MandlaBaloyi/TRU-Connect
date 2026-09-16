/** Trading Details — view-only summary. Edit lives on its own screen
 *  (my-business/trading-details.tsx). */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import type { TradingDetails } from "../../types";
import { EditButton } from "../EditButton";
import { categoryLabel } from "@/constants/productCategories";
import { RESTOCK_RHYTHM_LABELS, WEEKLY_SPEND_BAND_LABELS } from "../../types";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  trading: TradingDetails;
}

export function TradingDetailsSection({ trading }: Props) {
  const theme = useTheme();
  const router = useRouter();

  return (
    <View style={styles.viewMode}>
      {trading.buysCategories.length > 0 && (
        <View style={styles.summaryRow}>
          {/* "Buys", not "Sells". The question changed with the field:
              a salon sells haircuts and buys relaxers, and only the
              second is orderable here. */}
          <Text style={[styles.rowLabel, { color: theme.colors.onSurfaceVariant }]}>Buys</Text>
          <Text style={[styles.rowValue, { color: theme.colors.onSurface }]}>
            {trading.buysCategories.map((c) => categoryLabel(c)).join(", ")}
          </Text>
        </View>
      )}
      {trading.restockRhythm && (
        <View style={styles.summaryRow}>
          <Text style={[styles.rowLabel, { color: theme.colors.onSurfaceVariant }]}>Restocks</Text>
          <Text style={[styles.rowValue, { color: theme.colors.onSurface }]}>
            {RESTOCK_RHYTHM_LABELS[trading.restockRhythm]}
          </Text>
        </View>
      )}
      {trading.weeklySpendBand && (
        <View style={styles.summaryRow}>
          <Text style={[styles.rowLabel, { color: theme.colors.onSurfaceVariant }]}>Weekly stock spend</Text>
          <Text style={[styles.rowValue, { color: theme.colors.onSurface }]}>
            {WEEKLY_SPEND_BAND_LABELS[trading.weeklySpendBand]}
          </Text>
        </View>
      )}
      <EditButton onPress={() => router.push("/business/my-business/trading-details")} />
    </View>
  );
}

const styles = StyleSheet.create({
  viewMode: { gap: spacing.sm },
  summaryRow: { gap: 2 },
  rowLabel: { ...typography.bodySmall },
  rowValue: { ...typography.body },
});
