import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { OrderHistoryEvent } from "../types";
import { formatCents } from "../services/orderMapper";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  event: OrderHistoryEvent;
  customerName: string;
}

function labelFor(event: OrderHistoryEvent): string {
  switch (event.eventType) {
    case "ORDER_CREATED":
      return "Order placed";
    case "ORDER_COMPLETED":
      return "Order completed";
    case "ORDER_CANCELLED":
      return "Order cancelled";
    case "CUSTOMER_CREATED":
      return "New customer";
    default:
      return event.eventType;
  }
}

export function HistoryEventRow({ event, customerName }: Props) {
  const theme = useTheme();
  const time = new Date(event.occurredAt).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });

  return (
    <View style={styles.row}>
      <View style={styles.body}>
        <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={1}>
          {customerName}
        </Text>
        <Text style={[styles.meta, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
          {labelFor(event)} · {time}
          {event.reason ? ` · ${event.reason}` : ""}
        </Text>
      </View>
      {typeof event.amount === "number" && (
        <Text style={[styles.amount, { color: theme.colors.onSurface }]}>{formatCents(event.amount)}</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: spacing.sm, paddingVertical: spacing.sm, minHeight: 44 },
  body: { flex: 1, gap: 2 },
  name: { ...typography.body, fontWeight: "600" },
  meta: { ...typography.bodySmall },
  amount: { ...typography.body, fontWeight: "600" },
});
