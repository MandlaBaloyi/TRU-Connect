import React from "react";
import { ActivityIndicator, FlatList, Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { X } from "lucide-react-native";

import { formatCents } from "../../../supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useOrderHistory } from "../hooks/useOrderHistory";
import type { OrderHistoryEntry } from "../types";

interface Props {
  visible: boolean;
  supplierId: string;
  onClose: () => void;
}

const PAYMENT_METHOD_LABELS: Record<string, string> = {
  CASH: "Cash",
  PROOF_OF_PAYMENT: "Proof of Payment",
  PAYFAST: "Pay Online",
};

function formatDate(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

/** Reached from the cart's own 3-dot menu -- every order this
 *  business has actually submitted to this one supplier, most recent
 *  first. Read-only reference, not editable. */
export function OrderHistorySheet({ visible, supplierId, onClose }: Props) {
  const theme = useTheme();
  const { orders, isLoading } = useOrderHistory(supplierId);

  const renderItem = ({ item }: { item: OrderHistoryEntry }) => (
    <View style={[styles.row, { borderColor: theme.colors.outlineVariant }]}>
      <View style={styles.rowHeader}>
        <Text style={[styles.date, { color: theme.colors.onSurface }]}>{formatDate(item.submittedAt)}</Text>
        <Text style={[styles.total, { color: theme.colors.onSurface }]}>{formatCents(item.totalCents)}</Text>
      </View>
      <Text style={[styles.detail, { color: theme.colors.onSurfaceVariant }]}>
        {item.itemCount} {item.itemCount === 1 ? "item" : "items"} •{" "}
        {item.paymentMethod ? PAYMENT_METHOD_LABELS[item.paymentMethod] ?? item.paymentMethod : "—"} •{" "}
        {item.deliveryType === "COLLECT" ? "Collect" : "Deliver"}
      </Text>
    </View>
  );

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={styles.header}>
          <Text style={[styles.headerTitle, { color: theme.colors.onSurface }]}>Order History</Text>
          <Pressable onPress={onClose} hitSlop={10} accessibilityRole="button" accessibilityLabel="Close">
            <X size={22} color={theme.colors.onSurface} strokeWidth={2} />
          </Pressable>
        </View>

        {isLoading ? (
          <View style={styles.centre}>
            <ActivityIndicator color={theme.colors.primary} />
          </View>
        ) : orders.length === 0 ? (
          <View style={styles.centre}>
            <Text style={[styles.emptyText, { color: theme.colors.onSurfaceVariant }]}>
              No past orders with this supplier yet.
            </Text>
          </View>
        ) : (
          <FlatList
            data={orders}
            keyExtractor={(order) => order.id}
            contentContainerStyle={styles.list}
            renderItem={renderItem}
          />
        )}
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  headerTitle: { ...typography.h2, fontWeight: "700" },
  centre: { flex: 1, alignItems: "center", justifyContent: "center", padding: spacing.lg },
  emptyText: { ...typography.body, textAlign: "center" },
  list: { padding: spacing.md },
  row: { borderWidth: 1, borderRadius: radius.md, padding: spacing.md, marginBottom: spacing.sm, gap: 4 },
  rowHeader: { flexDirection: "row", justifyContent: "space-between" },
  date: { ...typography.body, fontWeight: "700" },
  total: { ...typography.body, fontWeight: "700" },
  detail: { ...typography.bodySmall },
});
