/** Trading Details — view-only summary. Edit lives on its own screen
 *  (my-business/trading-details.tsx). */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import type { TradingDetails } from "../../types";
import { EditButton } from "../EditButton";
import { CUSTOMER_TYPE_LABELS, ORDER_CHANNEL_LABELS, PAYMENT_METHOD_LABELS } from "../../types";
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
      {trading.products.length > 0 && (
        <View style={styles.summaryRow}>
          <Text style={[styles.rowLabel, { color: theme.colors.onSurfaceVariant }]}>Sells</Text>
          <Text style={[styles.rowValue, { color: theme.colors.onSurface }]}>{trading.products.join(", ")}</Text>
        </View>
      )}
      {trading.customerTypes.length > 0 && (
        <View style={styles.summaryRow}>
          <Text style={[styles.rowLabel, { color: theme.colors.onSurfaceVariant }]}>Customers</Text>
          <Text style={[styles.rowValue, { color: theme.colors.onSurface }]}>{trading.customerTypes.map((t) => CUSTOMER_TYPE_LABELS[t]).join(", ")}</Text>
        </View>
      )}
      {trading.orderChannels.length > 0 && (
        <View style={styles.summaryRow}>
          <Text style={[styles.rowLabel, { color: theme.colors.onSurfaceVariant }]}>Orders</Text>
          <Text style={[styles.rowValue, { color: theme.colors.onSurface }]}>{trading.orderChannels.map((c) => ORDER_CHANNEL_LABELS[c]).join(", ")}</Text>
        </View>
      )}
      {trading.paymentMethods.length > 0 && (
        <View style={styles.summaryRow}>
          <Text style={[styles.rowLabel, { color: theme.colors.onSurfaceVariant }]}>Payments</Text>
          <Text style={[styles.rowValue, { color: theme.colors.onSurface }]}>{trading.paymentMethods.map((p) => PAYMENT_METHOD_LABELS[p]).join(", ")}</Text>
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
