import React, { useState } from "react";
import { ActivityIndicator, Alert, Image, Modal, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useTheme } from "react-native-paper";
import { StatusBar } from "expo-status-bar";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, XCircle } from "lucide-react-native";

import { formatCents } from "../../../supplier/products/services/productMapper";
import * as supplierSearchService from "../../find-supplier/services/supplierSearchService";
import { ContactSupplierSheet } from "../../my-suppliers/components/ContactSupplierSheet";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import { palette } from "@/theme/colors";

import { useOrderDetail } from "../hooks/useOrderDetail";
import { useCancelOrder } from "../hooks/useCancelOrder";
import { CancelReasonSheet } from "./CancelReasonSheet";
import { ANY_CANCEL_REASON_LABELS, DECLINE_REASON_LABELS, getStatusLabel } from "../types";
import type { CancelReason } from "../types";
import { paymentMethodLabel } from "@/features/dashboard/shared/payment/paymentMethods";

interface Props {
  visible: boolean;
  supplierId: string;
  orderId: string | null;
  onClose: () => void;
}


/** Same date convention as OrderHistorySheet's own formatDate,
 *  extended with a time -- the exact moment matters here (how long a
 *  business waited on a decision), not just the day. */
function formatDateTime(iso: string | null): string {
  if (!iso) return "";
  const date = new Date(iso);
  return `${date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}, ${date.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}`;
}

/** One color per real outcome, not a spectrum -- PENDING is warning
 *  (genuinely undecided, not bad news), CONFIRMED is success,
 *  DECLINED/CANCELLED are the two ways an order didn't go ahead. */
function statusColor(status: string): string {
  if (status === "CONFIRMED") return palette.success;
  if (status === "DECLINED" || status === "CANCELLED") return palette.danger;
  return palette.warning; // PENDING_SUPPLIER_APPROVAL, AWAITING_PAYMENT
}

/** Reached by tapping into one row of OrderHistorySheet -- the real
 *  line items, the real status, the real address for one specific
 *  past order.
 *
 * STATUS LIVES AT THE BOTTOM NOW, ITS OWN SECTION -- moved off the
 * cramped top-right corner next to the order reference after direct
 * feedback that the two competing there read as one confusing line.
 * Color-coded (see statusColor above) so PENDING/CONFIRMED/DECLINED
 * are visually distinct at a glance, not just by wording. When
 * DECLINED, the supplier's own real reason (and free-text details, if
 * they gave one) show directly underneath -- this is real data that
 * already existed on the backend for the supplier's own side, simply
 * not surfaced to the business until now.
 *
 * SafeAreaView imported from react-native-safe-area-context, NOT
 * react-native's own -- confirmed via direct device report that the
 * core one is a no-op on Android, letting this header run under the
 * status bar. The <StatusBar> override exists for the matching
 * reason on the other axis: a full-screen Modal doesn't inherit the
 * app-level StatusBar style on Android.
 */
export function OrderDetailSheet({ visible, supplierId, orderId, onClose }: Props) {
  const theme = useTheme();
  const { order, isLoading, isError } = useOrderDetail(supplierId, orderId);
  const { cancelOrder, isCancelling } = useCancelOrder(supplierId, orderId ?? "");
  const [cancelSheetOpen, setCancelSheetOpen] = useState(false);
  const [contactSheetOpen, setContactSheetOpen] = useState(false);

  // Only fetched once this order is actually CONFIRMED -- that's the
  // one state where the business can no longer self-cancel and needs
  // a real way to reach the supplier instead (see this file's own
  // module docstring).
  const { data: supplierProfile } = useQuery({
    queryKey: ["orders", "supplier-contact", supplierId],
    queryFn: () => supplierSearchService.getSupplierProfile(supplierId),
    enabled: visible && order?.status === "CONFIRMED",
  });

  const handleCancel = async (reason: CancelReason, details?: string) => {
    try {
      await cancelOrder({ reason, details });
      setCancelSheetOpen(false);
    } catch {
      Alert.alert("Couldn't cancel order", "Check your connection and try again.");
    }
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      {visible && <StatusBar style={theme.dark ? "light" : "dark"} />}
      <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={[styles.header, { borderBottomColor: theme.colors.outlineVariant }]}>
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
            <Text style={[styles.orderIdLabel, { color: theme.colors.onSurface }]} selectable>
              Order ID: {order.orderReference}
            </Text>
            {order.submittedAt && (
              <Text style={[styles.submittedText, { color: theme.colors.onSurfaceVariant }]}>
                Submitted {formatDateTime(order.submittedAt)}
              </Text>
            )}

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
                <View style={[styles.imageWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
                  {item.images[0] && (
                    <Image source={{ uri: item.images[0] }} style={styles.image} resizeMode="contain" />
                  )}
                </View>
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
              {paymentMethodLabel(order.paymentMethod)}
            </Text>

            <Text style={[styles.sectionTitle, styles.sectionSpacing, { color: theme.colors.onSurface }]}>Status</Text>
            <View
              style={[
                styles.statusBadge,
                { backgroundColor: statusColor(order.status) + "22", borderColor: statusColor(order.status) },
              ]}
            >
              <View style={[styles.statusDot, { backgroundColor: statusColor(order.status) }]} />
              <Text style={[styles.statusBadgeText, { color: statusColor(order.status) }]}>
                {getStatusLabel(order.status)}
              </Text>
            </View>
            {order.decidedAt && (
              <Text style={[styles.processedText, { color: theme.colors.onSurfaceVariant }]}>
                Processed {formatDateTime(order.decidedAt)}
              </Text>
            )}
            {order.status === "DECLINED" && order.declineReason && (
              <View style={styles.declineExplanation}>
                <Text style={[styles.declineReasonText, { color: theme.colors.onSurface }]}>
                  Reason: {DECLINE_REASON_LABELS[order.declineReason]}
                </Text>
                {order.declineDetails && (
                  <Text style={[styles.plainTextSecondary, { color: theme.colors.onSurfaceVariant }]}>
                    {order.declineDetails}
                  </Text>
                )}
              </View>
            )}
            {order.status === "CANCELLED" && (
              <View style={styles.declineExplanation}>
                <Text style={[styles.declineReasonText, { color: theme.colors.onSurface }]}>
                  {order.cancelledBy === "supplier" ? "Cancelled by your supplier" : "Cancelled by you"}
                </Text>
                {order.cancelReason && (
                  <Text style={[styles.plainTextSecondary, { color: theme.colors.onSurfaceVariant }]}>
                    Reason: {ANY_CANCEL_REASON_LABELS[order.cancelReason] ?? order.cancelReason}
                  </Text>
                )}
              </View>
            )}

            {order.status === "PENDING_SUPPLIER_APPROVAL" && (
              <Pressable
                onPress={() => setCancelSheetOpen(true)}
                style={[styles.cancelButton, { borderColor: theme.colors.error }]}
                accessibilityRole="button"
                accessibilityLabel="Cancel order"
              >
                <XCircle size={18} color={theme.colors.error} strokeWidth={2.2} />
                <Text style={[styles.cancelButtonLabel, { color: theme.colors.error }]}>Cancel order</Text>
              </Pressable>
            )}

            {order.status === "CONFIRMED" && (
              <View style={[styles.contactNotice, { borderColor: theme.colors.outline, backgroundColor: theme.colors.surfaceVariant }]}>
                <Text style={[styles.plainTextSecondary, { color: theme.colors.onSurfaceVariant }]}>
                  This order's already been approved -- it can't be cancelled here anymore. Need to change or cancel
                  it? Contact your supplier directly.
                </Text>
                <Pressable
                  onPress={() => setContactSheetOpen(true)}
                  style={[styles.contactButton, { borderColor: theme.colors.outline }]}
                  accessibilityRole="button"
                  accessibilityLabel="Contact your supplier"
                >
                  <Text style={[styles.contactButtonLabel, { color: theme.colors.primary }]}>Contact supplier</Text>
                </Pressable>
              </View>
            )}
          </ScrollView>
        )}
      </SafeAreaView>

      <CancelReasonSheet
        visible={cancelSheetOpen}
        isSubmitting={isCancelling}
        onSubmit={handleCancel}
        onClose={() => setCancelSheetOpen(false)}
      />
      <ContactSupplierSheet
        visible={contactSheetOpen}
        supplierName={supplierProfile?.businessName || "your supplier"}
        contact={supplierProfile?.contact ?? null}
        onClose={() => setContactSheetOpen(false)}
      />
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
  orderIdLabel: { ...typography.h2, fontWeight: "700", marginBottom: 2 },
  submittedText: { ...typography.bodySmall, marginBottom: spacing.md },
  processedText: { ...typography.bodySmall, marginTop: spacing.xs },
  sectionTitle: { ...typography.h2, fontWeight: "700", marginBottom: spacing.sm },
  sectionSpacing: { marginTop: spacing.lg },
  itemRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm, paddingVertical: 4 },
  imageWrap: { width: 44, height: 44, borderRadius: radius.md, alignItems: "center", justifyContent: "center", overflow: "hidden" },
  image: { width: "100%", height: "100%" },
  itemLabel: { ...typography.body, flex: 1, paddingRight: spacing.sm },
  itemValue: { ...typography.body, fontWeight: "600" },
  divider: { height: StyleSheet.hairlineWidth, marginVertical: spacing.sm },
  totalLabel: { ...typography.body, fontWeight: "700" },
  totalValue: { ...typography.body, fontWeight: "700" },
  plainText: { ...typography.body },
  plainTextSecondary: { ...typography.bodySmall, marginTop: 2 },
  statusBadge: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    gap: spacing.xs,
    borderWidth: 1,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
  },
  statusDot: { width: 8, height: 8, borderRadius: 4 },
  statusBadgeText: { ...typography.body, fontWeight: "700" },
  declineExplanation: { marginTop: spacing.sm, gap: 2 },
  declineReasonText: { ...typography.body, fontWeight: "600" },
  cancelButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.xs,
    minHeight: 48,
    borderWidth: 1,
    borderRadius: radius.md,
    marginTop: spacing.lg,
  },
  cancelButtonLabel: { ...typography.body, fontWeight: "700" },
  contactNotice: { marginTop: spacing.lg, borderWidth: 1, borderRadius: radius.md, padding: spacing.md, gap: spacing.sm },
  contactButton: {
    alignSelf: "flex-start",
    minHeight: 40,
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    alignItems: "center",
    justifyContent: "center",
  },
  contactButtonLabel: { ...typography.body, fontWeight: "700" },
});
