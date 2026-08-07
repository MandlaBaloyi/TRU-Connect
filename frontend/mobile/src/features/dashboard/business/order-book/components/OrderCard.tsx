/**
 * OrderCard — one order in the queue. Theme-aware.
 *
 * Right column stacks order number (bold) directly above the price —
 * per feedback, replacing the earlier same-line placement. Left side
 * (customer name + item summary) is unchanged in position; the item
 * summary now derives from the order's actual line items via
 * formatItemSummary() rather than a separate typed order name.
 */

import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { OrderView } from "../types";
import { formatCents, formatItemSummary, formatOrderNumber } from "../services/orderMapper";
import { CustomerAvatar } from "./CustomerAvatar";
import { OrderStatusBadge } from "./OrderStatusBadge";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  view: OrderView;
  onPress?: () => void;
}

export function OrderCard({ view, onPress }: Props) {
  const theme = useTheme();
  const { order, customer } = view;
  const itemSummary = formatItemSummary(order.lineItems);

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
      accessibilityRole="button"
      accessibilityLabel={`Order ${formatOrderNumber(order)} for ${customer.name}, ${itemSummary}, ${formatCents(order.total)}`}
    >
      <CustomerAvatar name={customer.name} seed={customer.id} />
      <View style={styles.body}>
        <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={1}>
          {customer.name}
        </Text>
        <Text style={[styles.meta, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
          {itemSummary}
        </Text>
        <OrderStatusBadge status={order.status} />
      </View>
      <View style={styles.amountColumn}>
        <Text style={[styles.orderNumber, { color: theme.colors.onSurface }]} numberOfLines={1}>
          {formatOrderNumber(order)}
        </Text>
        <Text style={[styles.amount, { color: theme.colors.onSurface }]} numberOfLines={1}>
          {formatCents(order.total)}
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    paddingVertical: spacing.sm,
    minHeight: 44,
  },
  pressed: { opacity: 0.7 },
  body: { flex: 1, gap: 4 },
  name: { ...typography.h2 },
  meta: { ...typography.bodySmall },
  amountColumn: { alignItems: "flex-end", gap: 2 },
  orderNumber: { ...typography.body, fontWeight: "800" },
  amount: { ...typography.h2, fontWeight: "700" },
});
