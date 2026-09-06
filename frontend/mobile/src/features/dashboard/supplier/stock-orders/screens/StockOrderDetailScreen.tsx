import React, { useState } from "react";
import { ActivityIndicator, Alert, Image, Linking, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Mail, Phone, CheckCircle2, XCircle } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";
import { ErrorState } from "@/components/feedback/ErrorState";
import { formatCents } from "../../products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import { palette } from "@/theme/colors";

import { useOrderDetail } from "../hooks/useOrderDetail";
import { useOrderDecision } from "../hooks/useOrderDecision";
import { DeclineReasonSheet } from "../components/DeclineReasonSheet";
import { CancelReasonSheet } from "../components/CancelReasonSheet";
import { ANY_CANCEL_REASON_LABELS, DECLINE_REASON_LABELS, getStatusLabel } from "../types";
import type { CancelReason, DeclineReason } from "../types";

const PAYMENT_METHOD_LABELS: Record<string, string> = {
  CASH: "Cash",
  PROOF_OF_PAYMENT: "Proof of Payment",
  PAYFAST: "Pay Online",
};

/** Same convention as business/orders' own OrderDetailSheet --
 *  duplicated locally rather than shared across the domain boundary,
 *  same reasoning as DECLINE_REASON_LABELS/statusColor above. */
function formatDateTime(iso: string | null): string {
  if (!iso) return "";
  const date = new Date(iso);
  return `${date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}, ${date.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}`;
}

/** One color per real outcome, matching business/orders' own
 *  OrderDetailSheet exactly (duplicated rather than shared across the
 *  domain boundary, same reasoning as DECLINE_REASON_LABELS above) --
 *  PENDING is warning (genuinely undecided, not bad news), CONFIRMED
 *  is success, DECLINED/CANCELLED are the two ways an order didn't go
 *  ahead. Real, exhaustive per-status mapping -- NOT the previous
 *  isPending/isConfirmed/else chain, which silently mislabeled
 *  CANCELLED as "Declined" (see StockOrderStatus's own comment). */
function statusColor(status: string): string {
  if (status === "CONFIRMED") return palette.success;
  if (status === "DECLINED" || status === "CANCELLED") return palette.danger;
  return palette.warning;
}

/**
 * The real order detail -- everything a supplier needs to genuinely
 * decide: the buyer, the items, the price, how they'll pay, how it's
 * getting there, and a real, working way to call the business
 * directly. Approve/Decline only show while the order is genuinely
 * still pending -- once decided, this becomes a clean, real record of
 * what happened.
 *
 * STATUS LIVES AT THE BOTTOM, ITS OWN SECTION -- matches business/
 * orders' own OrderDetailSheet after direct feedback that a status
 * banner competing for attention at the very top read as cluttered.
 * Header title is a stable "Order" (matching the loading/error
 * states already used below) rather than the order reference itself
 * -- no title flicker as the real reference loads in, and the
 * reference now gets an explicit "Order ID:" label in the content,
 * same as the business side.
 */
export default function StockOrderDetailScreen() {
  const { orderId } = useLocalSearchParams<{ orderId: string }>();
  const router = useRouter();
  const theme = useTheme();
  const { order, isLoading, isError, refetch } = useOrderDetail(orderId ?? "");
  const { approveOrder, isApproving, declineOrder, isDeclining, cancelOrder, isCancelling } = useOrderDecision(
    orderId ?? ""
  );
  const [declineSheetOpen, setDeclineSheetOpen] = useState(false);
  const [cancelSheetOpen, setCancelSheetOpen] = useState(false);

  const handleApprove = () => {
    Alert.alert("Approve this order?", "The business will be notified right away.", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Approve",
        onPress: async () => {
          try {
            await approveOrder();
            router.back();
          } catch {
            Alert.alert("Couldn't approve order", "Check your connection and try again.");
          }
        },
      },
    ]);
  };

  const handleDecline = async (reason: DeclineReason, details?: string) => {
    try {
      await declineOrder({ reason, details });
      setDeclineSheetOpen(false);
      router.back();
    } catch {
      Alert.alert("Couldn't decline order", "Check your connection and try again.");
    }
  };

  const handleCancel = async (reason: CancelReason, details?: string) => {
    try {
      await cancelOrder({ reason, details });
      setCancelSheetOpen(false);
      router.back();
    } catch {
      Alert.alert("Couldn't cancel order", "Check your connection and try again.");
    }
  };

  const handleCall = () => {
    if (!order?.buyerPhone) return;
    Linking.openURL(`tel:${order.buyerPhone}`).catch(() => {
      // Silently ignored -- no dialer available is nothing more useful to act on.
    });
  };

  const handleEmail = () => {
    if (!order?.buyerEmail) return;
    Linking.openURL(`mailto:${order.buyerEmail}`).catch(() => {
      // Silently ignored, same reasoning as handleCall above.
    });
  };

  if (isLoading) {
    return (
      <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
        <AppHeader variant="title" title="Order" showBackButton />
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !order) {
    return (
      <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
        <AppHeader variant="title" title="Order" showBackButton />
        <ErrorState message="Couldn't load this order. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const isPending = order.status === "PENDING_SUPPLIER_APPROVAL";
  const isConfirmed = order.status === "CONFIRMED";

  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      <AppHeader variant="title" title="Order" showBackButton />

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
        <View style={[styles.buyerCard, { borderColor: theme.colors.outlineVariant }]}>
          <View style={styles.buyerHeaderRow}>
            <View style={styles.buyerText}>
              <Text style={[styles.buyerName, { color: theme.colors.onSurface }]}>
                {order.buyerBusinessName || order.buyerName || "A business"}
              </Text>
              {order.buyerBusinessName && order.buyerName && (
                <Text style={[styles.buyerSubtext, { color: theme.colors.onSurfaceVariant }]}>{order.buyerName}</Text>
              )}
            </View>
          </View>

          {order.buyerPhone && (
            <View style={styles.contactRow}>
              <Text style={[styles.contactValue, { color: theme.colors.onSurface }]}>{order.buyerPhone}</Text>
              <Pressable
                onPress={handleCall}
                style={[styles.contactButton, { backgroundColor: theme.colors.primaryContainer }]}
                accessibilityRole="button"
                accessibilityLabel="Call"
              >
                <Phone size={16} color={theme.colors.primary} strokeWidth={2.2} />
              </Pressable>
            </View>
          )}

          {order.buyerEmail && (
            <View style={styles.contactRow}>
              <Text style={[styles.contactValue, { color: theme.colors.onSurface }]} numberOfLines={1}>
                {order.buyerEmail}
              </Text>
              <Pressable
                onPress={handleEmail}
                style={[styles.contactButton, { backgroundColor: theme.colors.primaryContainer }]}
                accessibilityRole="button"
                accessibilityLabel="Email"
              >
                <Mail size={16} color={theme.colors.primary} strokeWidth={2.2} />
              </Pressable>
            </View>
          )}
        </View>

        <Text style={[styles.sectionTitle, styles.sectionSpacing, { color: theme.colors.onSurface }]}>Items</Text>
        {order.items.map((item) => (
          <View key={item.productId} style={styles.itemRow}>
            <View style={[styles.imageWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
              {item.images[0] && <Image source={{ uri: item.images[0] }} style={styles.image} resizeMode="contain" />}
            </View>
            <Text style={[styles.itemLabel, { color: theme.colors.onSurface }]} numberOfLines={1}>
              {item.quantity} × {item.productName}
            </Text>
            <Text style={[styles.itemValue, { color: theme.colors.onSurface }]}>{formatCents(item.lineTotalCents)}</Text>
          </View>
        ))}
        <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />
        <View style={styles.itemRow}>
          <Text style={[styles.totalLabel, { color: theme.colors.onSurface }]}>Total</Text>
          <Text style={[styles.totalValue, { color: theme.colors.onSurface }]}>{formatCents(order.totalCents)}</Text>
        </View>

        <Text style={[styles.sectionTitle, styles.sectionSpacing, { color: theme.colors.onSurface }]}>Payment</Text>
        <Text style={[styles.plainText, { color: theme.colors.onSurface }]}>
          {order.paymentMethod ? PAYMENT_METHOD_LABELS[order.paymentMethod] ?? order.paymentMethod : "—"}
        </Text>

        <Text style={[styles.sectionTitle, styles.sectionSpacing, { color: theme.colors.onSurface }]}>
          {order.deliveryType === "COLLECT" ? "Collection" : "Delivery"}
        </Text>
        <Text style={[styles.plainText, { color: theme.colors.onSurface }]}>{order.deliveryAddressText || "—"}</Text>

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
              {order.cancelledBy === "business" ? "Cancelled by the business" : "Cancelled by you"}
            </Text>
            {order.cancelReason && (
              <Text style={[styles.plainTextSecondary, { color: theme.colors.onSurfaceVariant }]}>
                Reason: {ANY_CANCEL_REASON_LABELS[order.cancelReason] ?? order.cancelReason}
              </Text>
            )}
          </View>
        )}
      </ScrollView>

      {isPending && (
        <View style={[styles.actionBar, { backgroundColor: theme.colors.surface, borderTopColor: theme.colors.outlineVariant }]}>
          <Pressable
            onPress={() => setDeclineSheetOpen(true)}
            disabled={isApproving}
            style={[styles.actionButton, styles.declineButton, { borderColor: theme.colors.error }]}
            accessibilityRole="button"
            accessibilityLabel="Decline"
          >
            <XCircle size={18} color={theme.colors.error} strokeWidth={2.2} />
            <Text style={[styles.actionLabel, { color: theme.colors.error }]}>Decline</Text>
          </Pressable>
          <Pressable
            onPress={handleApprove}
            disabled={isApproving}
            style={[styles.actionButton, styles.approveButton, { backgroundColor: theme.colors.primary }]}
            accessibilityRole="button"
            accessibilityLabel="Approve"
          >
            {isApproving ? (
              <ActivityIndicator color={theme.colors.onPrimary} />
            ) : (
              <>
                <CheckCircle2 size={18} color={theme.colors.onPrimary} strokeWidth={2.2} />
                <Text style={[styles.actionLabel, { color: theme.colors.onPrimary }]}>Approve</Text>
              </>
            )}
          </Pressable>
        </View>
      )}

      {isConfirmed && (
        <View style={[styles.actionBar, { backgroundColor: theme.colors.surface, borderTopColor: theme.colors.outlineVariant }]}>
          <Pressable
            onPress={() => setCancelSheetOpen(true)}
            style={[styles.actionButton, styles.declineButton, { borderColor: theme.colors.error, flex: 1 }]}
            accessibilityRole="button"
            accessibilityLabel="Cancel order"
          >
            <XCircle size={18} color={theme.colors.error} strokeWidth={2.2} />
            <Text style={[styles.actionLabel, { color: theme.colors.error }]}>Cancel order</Text>
          </Pressable>
        </View>
      )}

      <DeclineReasonSheet
        visible={declineSheetOpen}
        isSubmitting={isDeclining}
        onSubmit={handleDecline}
        onClose={() => setDeclineSheetOpen(false)}
      />
      <CancelReasonSheet
        visible={cancelSheetOpen}
        isSubmitting={isCancelling}
        onSubmit={handleCancel}
        onClose={() => setCancelSheetOpen(false)}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  content: { padding: spacing.md, paddingBottom: 100 },
  orderIdLabel: { ...typography.h2, fontWeight: "700", marginBottom: 2 },
  submittedText: { ...typography.bodySmall, marginBottom: spacing.md },
  processedText: { ...typography.bodySmall, marginTop: spacing.xs },
  sectionTitle: { ...typography.h2, fontWeight: "700", marginBottom: spacing.sm },
  sectionSpacing: { marginTop: spacing.lg },
  buyerCard: {
    borderWidth: 1,
    borderRadius: radius.md,
    padding: spacing.sm,
    gap: spacing.xs,
  },
  buyerHeaderRow: { flexDirection: "row", alignItems: "center" },
  buyerText: { flex: 1, gap: 2 },
  buyerName: { ...typography.body, fontWeight: "700" },
  buyerSubtext: { ...typography.bodySmall },
  contactRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: spacing.sm },
  contactValue: { ...typography.body, flex: 1 },
  contactButton: { width: 36, height: 36, borderRadius: radius.pill, alignItems: "center", justifyContent: "center" },
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
  actionBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: "row",
    gap: spacing.sm,
    padding: spacing.md,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  actionButton: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.xs,
    minHeight: 48,
    borderRadius: radius.md,
  },
  declineButton: { borderWidth: 1.5 },
  approveButton: {},
  actionLabel: { fontWeight: "700", fontSize: 15 },
});
