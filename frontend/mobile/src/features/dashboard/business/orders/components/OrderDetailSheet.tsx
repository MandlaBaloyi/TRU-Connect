import React from "react";
import { ActivityIndicator, Modal, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { ChevronLeft } from "lucide-react-native";

import { formatCents } from "../../../supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import { palette } from "@/theme/colors";

import { useOrderDetail } from "../hooks/useOrderDetail";
import { getStatusLabel } from "../types";

interface Props {
  visible: boolean;
  supplierId: string;
  orderId: string | null;
  onClose: () => void;
}

const PAYMENT_METHOD_LABELS: Record<string, string> = {
  CASH: "Cash",
  PROOF_OF_PAYMENT: "Proof of Payment",
  PAYFAST: "Pay Online",
};

function statusColor(status: string, errorColor: string, onSurfaceColor: string): string {
  if (status === "CONFIRMED") return palette.success;
  if (status === "DECLINED" || status === "CANCELLED") return errorColor;
  return onSurfaceColor; // PENDING_SUPPLIER_APPROVAL and others -- neutral, not yet a final outcome
}

/** Reached by tapping into one row of OrderHistorySheet -- the real
 *  line items, the real status, the real address for one specific
 *  past order. */
export function OrderDetailSheet({ visible, supplierId, orderId, onClose }: Props) {
  const theme = useTheme();
  const { order, isLoading, isError } = useOrderDetail(supplierId, orderId);

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={styles.header}>
          <Pressable onPress={onClose} hitSlop={10} accessibilityRole="button" accessibilityLabel="Back">
            <ChevronLeft size={26} color={theme.colors.onSurface} strokeWidth={2.8} />
          </Pressable>
          <Text style={[styles.headerTitle, { color: theme.colors.onSurface }]}>Order Details</Text>
          <View style={{ width: 26 }} />
        </View>

        {isLoading ? (
          <View style={styles.centre}>
            <ActivityIndicator color={theme.colors.primary} />
          </View>
        ) : isError || !order ? (
          <View style={styles.centre}>
            <Text style={[styles.emptyText, { color: theme.colors.onSurfaceVariant }]}>Couldn't load this order.</Text>
          </View>
        ) : (
          <ScrollView contentContainerStyle={styles.content}>
            <View style={styles.statusRow}>
              <Text style={[styles.orderReference, { color: theme.colors.onSurfaceVariant }]} selectable>
                {order.orderReference}
              </Text>
              <Text style={[styles.status, { color: statusColor(order.status, theme.colors.error, theme.colors.onSurface) }]}>
                {getStatusLabel(order.status)}
              </Text>
            </View>

            <Text style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>Ordered by</Text>
            <Text style={[styles.plainText, { color: theme.colors.onSurface }]}>
              {order.buyerBusinessName || order.buyerName || "—"}
            </Text>
            {order.buyerName && order.buyerBusinessName ? (
              <Text style={[styles.plainTextSecondary, { color: theme.colors.onSurfaceVariant }]}>
                {order.buyerName}
              </Text>
            ) : null}
            {order.buyerPhone ? (
              <Text style={[styles.plainTextSecondary, { color: theme.colors.onSurfaceVariant }]}>
                {order.buyerPhone}
              </Text>
            ) : null}
            {order.buyerEmail ? (
              <Text style={[styles.plainTextSecondary, { color: theme.colors.onSurfaceVariant }]}>
                {order.buyerEmail}
              </Text>
            ) : null}

            <Text style={[styles.sectionTitle, styles.sectionSpacing, { color: theme.colors.onSurface }]}>Items</Text>
            {order.items.map((item) => (
              <View key={item.productId} style={styles.itemRow}>
                <Text style={[styles.itemLabel, { color: theme.colors.onSurface }]} numberOfLines={1}>
                  {item.quantity} × {item.productName}
                </Text>
                <Text style={[styles.itemValue, { color: theme.colors.onSurface }]}>
                  {formatCents(item.lineTotalCents)}
                </Text>
              </View>
            ))}
            <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />
            <View style={styles.itemRow}>
              <Text style={[styles.totalLabel, { color: theme.colors.onSurface }]}>Total</Text>
              <Text style={[styles.totalValue, { color: theme.colors.onSurface }]}>{formatCents(order.totalCents)}</Text>
            </View>

            <Text style={[styles.sectionTitle, styles.sectionSpacing, { color: theme.colors.onSurface }]}>
              {order.deliveryType === "COLLECT" ? "Collection address" : "Delivery address"}
            </Text>
            <Text style={[styles.plainText, { color: theme.colors.onSurface }]}>
              {order.deliveryAddressText || "—"}
            </Text>

            <Text style={[styles.sectionTitle, styles.sectionSpacing, { color: theme.colors.onSurface }]}>
              Payment method
            </Text>
            <Text style={[styles.plainText, { color: theme.colors.onSurface }]}>
              {order.paymentMethod ? PAYMENT_METHOD_LABELS[order.paymentMethod] ?? order.paymentMethod : "—"}
            </Text>
          </ScrollView>
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
  content: { padding: spacing.md, paddingBottom: spacing.xl },
  statusRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.md },
  orderReference: { ...typography.caption, fontWeight: "600" },
  status: { ...typography.body, fontWeight: "700" },
  sectionTitle: { ...typography.h2, fontWeight: "700", marginBottom: spacing.sm },
  sectionSpacing: { marginTop: spacing.lg },
  itemRow: { flexDirection: "row", justifyContent: "space-between", paddingVertical: 4 },
  itemLabel: { ...typography.body, flex: 1, paddingRight: spacing.sm },
  itemValue: { ...typography.body, fontWeight: "600" },
  divider: { height: StyleSheet.hairlineWidth, marginVertical: spacing.sm },
  totalLabel: { ...typography.body, fontWeight: "700" },
  totalValue: { ...typography.body, fontWeight: "700" },
  plainText: { ...typography.body },
  plainTextSecondary: { ...typography.bodySmall, marginTop: 2 },
});
