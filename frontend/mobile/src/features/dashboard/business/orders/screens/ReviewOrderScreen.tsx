import React, { useLayoutEffect } from "react";
import { ActivityIndicator, Alert, Image, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useNavigation, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { ApiError } from "@/services/api/apiClient";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { EntityHeaderTitle } from "@/components/navigation/EntityHeaderTitle";
import { formatCents } from "../../../supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useCart } from "../hooks/useCart";
import { useSupplierIdentity } from "../hooks/useSupplierIdentity";
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
  const {
    supplierId,
    paymentMethod,
    deliveryType,
    deliveryAddressText,
    deliveryBuilding,
    deliveryStreet,
    deliverySuburb,
    deliveryCity,
    deliveryProvince,
    deliveryPostalCode,
    deliveryLatitude,
    deliveryLongitude,
  } = useLocalSearchParams<{
    supplierId: string;
    paymentMethod: PaymentMethod;
    deliveryType: DeliveryType;
    deliveryAddressText: string;
    deliveryBuilding?: string;
    deliveryStreet?: string;
    deliverySuburb?: string;
    deliveryCity?: string;
    deliveryProvince?: string;
    deliveryPostalCode?: string;
    deliveryLatitude?: string;
    deliveryLongitude?: string;
  }>();
  const router = useRouter();
  const navigation = useNavigation();
  const theme = useTheme();
  const { cart, isLoading, isError, refetch } = useCart(supplierId ?? "");
  // Reads the supplier from the cart when there is one, and from
  // their profile when there is not -- an empty cart must not blank
  // the header. See useSupplierIdentity.
  const supplier = useSupplierIdentity(supplierId ?? "");
  const { submitCheckout, isSubmitting } = useCheckout(supplierId ?? "");

  /* THE SAME SOCIAL TOP BAR AS THE CART, carried to the last step.
     This is the screen where the order is actually submitted, so being
     certain WHO it is going to matters more here than anywhere else in
     the flow -- and it is the one place a mistake cannot be walked
     back with the chevron. See DeliveryPaymentScreen for the rest of
     the reasoning; the two are deliberately identical. */
  useLayoutEffect(() => {
    navigation.setOptions({
      ...(supplier.name
        ? {
            headerTitle: () => (
              <EntityHeaderTitle name={supplier.name!} subtitle="Review order" photoUrl={supplier.photoUrl} />
            ),
          }
        : {}),
    });
  }, [navigation, supplier.name, supplier.photoUrl]);

  const handleConfirm = async () => {
    try {
      const result = await submitCheckout({
        paymentMethod,
        deliveryType,
        deliveryAddressText,
        // Router params are always strings or undefined -- only ever
        // present when DeliveryPaymentScreen actually sent them
        // (DELIVER with a confirmed map pin); undefined here is
        // exactly what submitCheckout already treats as "not sent".
        deliveryBuilding,
        deliveryStreet,
        deliverySuburb,
        deliveryCity,
        deliveryProvince,
        deliveryPostalCode,
        deliveryLatitude: deliveryLatitude ? Number(deliveryLatitude) : undefined,
        deliveryLongitude: deliveryLongitude ? Number(deliveryLongitude) : undefined,
      });
      router.replace({
        pathname: `/business/orders/${supplierId}/placed` as any,
        params: {
          orderId: result.id,
          orderReference: result.orderReference,
          totalCents: String(result.totalCents),
          instructions: result.instructions ?? "",
          paymentMethod,
          supplierName: supplier.name ?? "",
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
  itemRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: spacing.sm, paddingVertical: 4 },
  imageWrap: { width: 44, height: 44, borderRadius: radius.md, alignItems: "center", justifyContent: "center", overflow: "hidden" },
  image: { width: "100%", height: "100%" },
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
