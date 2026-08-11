/**
 * OrderDetailScreen — one order. Complete/Cancel are the only actions,
 * and only shown for PENDING orders (backend rejects any other
 * transition regardless, but hiding the buttons here avoids a
 * confusing tap-then-error round trip for a transition that can never
 * succeed).
 */

import React, { useState } from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { useOrder, useOrderMutations, useTrash } from "../hooks";
import { formatCents, formatItemSummary, formatOrderNumber } from "../services/orderMapper";
import { CustomerAvatar, LineItemRow, OrderStatusBadge } from "../components";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SecondaryButton } from "@/components/ui/SecondaryButton";

export default function OrderDetailScreen() {
  const router = useRouter();
  const theme = useTheme();
  const { orderId } = useLocalSearchParams<{ orderId: string }>();
  const { view, isLoading, isError, refetch } = useOrder(orderId);
  const { completeOrder, isCompletingOrder, cancelOrder, isCancellingOrder } = useOrderMutations();
  const { deleteOrder, isDeletingOrder } = useTrash();

  const [showCancelReason, setShowCancelReason] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !view) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Could not load this order." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const { order, customer } = view;
  const isPending = order.status === "PENDING";

  const handleComplete = async () => {
    setActionError(null);
    try {
      await completeOrder(order.id);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Could not complete this order.");
    }
  };

  const handleCancel = async () => {
    setActionError(null);
    try {
      await cancelOrder({ orderId: order.id, reason: cancelReason.trim() || undefined });
      setShowCancelReason(false);
      setCancelReason("");
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Could not cancel this order.");
    }
  };

  const handleDelete = () => {
    Alert.alert(
      "Delete this order?",
      "It will move to Trash and can be restored within 7 days.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            setActionError(null);
            try {
              await deleteOrder(order.id);
              router.back();
            } catch (error) {
              setActionError(error instanceof Error ? error.message : "Could not delete this order.");
            }
          },
        },
      ]
    );
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.headerRow}>
          <CustomerAvatar name={customer.name} seed={customer.id} size={52} />
          <View style={styles.headerText}>
            <Text style={[styles.orderName, { color: theme.colors.onSurface }]} numberOfLines={1}>
              {formatItemSummary(order.lineItems)}
            </Text>
            <Text style={[styles.customerName, { color: theme.colors.onSurfaceVariant }]}>
              {customer.name}
              {customer.phone ? ` · ${customer.phone}` : ""}
            </Text>
          </View>
          <View style={styles.headerRight}>
            <Text style={[styles.orderNumber, { color: theme.colors.onSurface }]}>
              {formatOrderNumber(order)}
            </Text>
            <OrderStatusBadge status={order.status} />
          </View>
        </View>

        <View style={[styles.section, { borderColor: theme.colors.outline }]}>
          {order.lineItems.map((item) => (
            <LineItemRow
              key={item.id}
              description={item.description}
              quantity={item.quantity}
              unitPrice={item.unitPrice}
              lineTotal={item.lineTotal}
            />
          ))}
          <View style={[styles.totalRow, { borderTopColor: theme.colors.outline }]}>
            <Text style={[styles.totalLabel, { color: theme.colors.onSurfaceVariant }]}>Total</Text>
            <Text style={[styles.totalValue, { color: theme.colors.onSurface }]}>{formatCents(order.total)}</Text>
          </View>
        </View>

        {order.notes && (
          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Notes</Text>
            <Text style={[styles.notes, { color: theme.colors.onSurface }]}>{order.notes}</Text>
          </View>
        )}

        {order.status === "CANCELLED" && order.cancellationReason && (
          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Cancellation reason</Text>
            <Text style={[styles.notes, { color: theme.colors.onSurface }]}>{order.cancellationReason}</Text>
          </View>
        )}

        {actionError && <Text style={[styles.error, { color: theme.colors.error }]}>{actionError}</Text>}

        {isPending && !showCancelReason && (
          <View style={styles.actions}>
            <PrimaryButton onPress={handleComplete} loading={isCompletingOrder} disabled={isCompletingOrder || isCancellingOrder}>
              Mark completed
            </PrimaryButton>
            <SecondaryButton
              onPress={() => setShowCancelReason(true)}
              disabled={isCompletingOrder || isCancellingOrder}
            >
              Cancel order
            </SecondaryButton>
          </View>
        )}

        {isPending && showCancelReason && (
          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Why is this being cancelled? (optional)</Text>
            <TextInput
              value={cancelReason}
              onChangeText={setCancelReason}
              placeholder="Customer changed their mind"
              placeholderTextColor={theme.colors.onSurfaceVariant}
              style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            />
            <View style={styles.actions}>
              <PrimaryButton onPress={handleCancel} loading={isCancellingOrder} disabled={isCancellingOrder}>
                Confirm cancellation
              </PrimaryButton>
              <SecondaryButton onPress={() => setShowCancelReason(false)} disabled={isCancellingOrder}>
                Go back
              </SecondaryButton>
            </View>
          </View>
        )}

        <Pressable
          onPress={handleDelete}
          disabled={isDeletingOrder}
          style={styles.deleteLink}
          accessibilityRole="button"
          accessibilityLabel="Delete this order"
        >
          <Text style={[styles.deleteLinkText, { color: theme.colors.error }]}>
            {isDeletingOrder ? "Deleting…" : "Delete order"}
          </Text>
        </Pressable>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.lg },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  headerRow: { flexDirection: "row", alignItems: "center", gap: spacing.md },
  headerText: { flex: 1, gap: 2 },
  orderName: { ...typography.h1 },
  customerName: { ...typography.bodySmall },
  headerRight: { alignItems: "flex-end", gap: spacing.xs },
  orderNumber: { ...typography.h2, fontWeight: "800" },
  section: { borderWidth: 1, borderRadius: radius.md, padding: spacing.md, gap: spacing.xs },
  totalRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", borderTopWidth: StyleSheet.hairlineWidth, paddingTop: spacing.sm, marginTop: spacing.xs },
  totalLabel: { ...typography.body },
  totalValue: { ...typography.h1, fontWeight: "700" },
  field: { gap: spacing.sm },
  label: { ...typography.bodySmall },
  notes: { ...typography.body },
  input: { borderWidth: 1, borderRadius: radius.md, paddingHorizontal: spacing.md, minHeight: 48, ...typography.body },
  error: { ...typography.bodySmall },
  actions: { gap: spacing.sm },
  deleteLink: { alignSelf: "center", minHeight: 44, justifyContent: "center", paddingHorizontal: spacing.md, marginTop: spacing.sm },
  deleteLinkText: { ...typography.body, fontWeight: "600" },
});
