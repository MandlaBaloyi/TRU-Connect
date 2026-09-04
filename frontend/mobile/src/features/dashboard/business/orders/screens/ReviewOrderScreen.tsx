import React from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { ApiError } from "@/services/api/apiClient";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { formatCents } from "../../../supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useCart } from "../hooks/useCart";
import { useCheckout } from "../hooks/useCheckout";
import type { DeliveryType, PaymentMethod } from "../types";

const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  CASH: "Cash",
  PROOF_OF_PAYMENT: "Proof of Payment",
  PAYFAST: "Pay Online",
};

/**
 * Step 2 of 3 -- the real items, the real address, the real payment
 * choice, all shown together before anything is actually submitted.
 * THE REAL "Confirm Order" BUTTON lives here, not on the previous
 * screen -- this is the one moment the actual submit_checkout call
 * happens.
 *
 * "Edit cart" goes back to the cart itself, not just one step back --
 * a business reviewing their order and wanting to change an item
 * shouldn't have to re-walk delivery/payment just to get there.
 */
export default function ReviewOrderScreen() {
  const { supplierId, paymentMethod, deliveryType, deliveryAddressText } = useLocalSearchParams<{
    supplierId: string;
    paymentMethod: PaymentMethod;
    deliveryType: DeliveryType;
    deliveryAddressText: string;
  }>();
  const router = useRouter();
  const theme = useTheme();
  const { cart, isLoading, isError, refetch } = useCart(supplierId ?? "");
  const { submitCheckout, isSubmitting } = useCheckout(supplierId ?? "");

  const handleConfirm = async () => {
    try {
      const result = await submitCheckout({
        paymentMethod,
        deliveryType,
        deliveryAddressText,
      });
      router.replace({
        pathname: `/business/orders/${supplierId}/placed` as any,
        params: {
          orderId: result.id,
          orderReference: result.orderReference,
          totalCents: String(result.totalCents),
          instructions: result.instructions ?? "",
          paymentMethod,
          supplierName: cart?.supplierName ?? "",
        },
      });
    } catch (error) {
      // Real bug found and fixed after direct report: this used to
      // show a generic "check your connection" message for EVERY
      // failure, including real, specific backend rejections
      // (StaleCartItemError, OrderLimitExceededError,
      // CartAlreadySubmittedError, EmptyCartError) that already had
      // clear, correct messages -- those were being thrown away.
      if (error instanceof ApiError) {
        Alert.alert("Couldn't place order", error.message);
        return;
      }
      Alert.alert("Couldn't place order", "Check your connection and try again.");
    }
  };

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !cart) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load your cart. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.sectionHeaderRow}>
          <Text style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>Items</Text>
          <Pressable onPress={() => router.back()} accessibilityRole="button" accessibilityLabel="Edit cart">
            <Text style={[styles.editLink, { color: theme.colors.primary }]}>Edit cart</Text>
          </Pressable>
        </View>
        {cart.items.map((item) => (
          <View key={item.productId} style={styles.itemRow}>
            <Text style={[styles.itemLabel, { color: theme.colors.onSurface }]} numberOfLines={1}>
              {item.quantity} × {item.productName}
            </Text>
            <Text style={[styles.itemValue, { color: theme.colors.onSurface }]}>{formatCents(item.lineTotalCents)}</Text>
          </View>
        ))}
        <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />
        <View style={styles.itemRow}>
          <Text style={[styles.totalLabel, { color: theme.colors.onSurface }]}>Total</Text>
          <Text style={[styles.totalValue, { color: theme.colors.onSurface }]}>{formatCents(cart.totalCents)}</Text>
        </View>

        <Text style={[styles.sectionTitle, styles.sectionSpacing, { color: theme.colors.onSurface }]}>
          {deliveryType === "COLLECT" ? "Collection address" : "Delivery address"}
        </Text>
        <Text style={[styles.plainText, { color: theme.colors.onSurface }]}>{deliveryAddressText}</Text>

        <Text style={[styles.sectionTitle, styles.sectionSpacing, { color: theme.colors.onSurface }]}>Payment method</Text>
        <Text style={[styles.plainText, { color: theme.colors.onSurface }]}>{PAYMENT_METHOD_LABELS[paymentMethod]}</Text>

        <Pressable
          onPress={handleConfirm}
          disabled={isSubmitting}
          style={[styles.confirmButton, { backgroundColor: theme.colors.primary }, isSubmitting && styles.confirmButtonDisabled]}
          accessibilityRole="button"
          accessibilityLabel="Confirm order"
        >
          {isSubmitting ? (
            <ActivityIndicator color={theme.colors.onPrimary} />
          ) : (
            <Text style={[styles.confirmLabel, { color: theme.colors.onPrimary }]}>Confirm Order</Text>
          )}
        </Pressable>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  content: { padding: spacing.md, paddingBottom: spacing.xl },
  sectionHeaderRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: spacing.sm },
  sectionTitle: { ...typography.h2, fontWeight: "700" },
  editLink: { ...typography.bodySmall, fontWeight: "700", textDecorationLine: "underline" },
  sectionSpacing: { marginTop: spacing.lg, marginBottom: spacing.sm },
  itemRow: { flexDirection: "row", justifyContent: "space-between", paddingVertical: 4 },
  itemLabel: { ...typography.body, flex: 1, paddingRight: spacing.sm },
  itemValue: { ...typography.body, fontWeight: "600" },
  divider: { height: StyleSheet.hairlineWidth, marginVertical: spacing.sm },
  totalLabel: { ...typography.body, fontWeight: "700" },
  totalValue: { ...typography.body, fontWeight: "700" },
  plainText: { ...typography.body },
  confirmButton: { marginTop: spacing.xl, minHeight: 48, borderRadius: radius.md, alignItems: "center", justifyContent: "center" },
  confirmButtonDisabled: { opacity: 0.6 },
  confirmLabel: { fontWeight: "700", fontSize: 16 },
});
