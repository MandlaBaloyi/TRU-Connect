import React, { useLayoutEffect, useState } from "react";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useNavigation } from "expo-router";
import { useTheme } from "react-native-paper";
import { Receipt } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { EmptyState } from "@/components/feedback/EmptyState";
import { ErrorState } from "@/components/feedback/ErrorState";
import { EntityHeaderTitle } from "@/components/navigation/EntityHeaderTitle";
import { formatCents } from "../../../supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useOrderHistory } from "../hooks/useOrderHistory";
import { useSupplierIdentity } from "../hooks/useSupplierIdentity";
import { OrderDetailSheet } from "../components/OrderDetailSheet";
import { getStatusLabel } from "../types";
import type { OrderHistoryEntry } from "../types";
import { paymentMethodLabel } from "@/features/dashboard/shared/payment/paymentMethods";


function formatDate(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

/**
 * Every order this business has placed with ONE supplier, most recent
 * first. Read-only reference, not editable.
 *
 * A REAL SCREEN, NOT A MODAL. This was a full-screen <Modal> opened
 * from the cart's ⋮ (OrderHistorySheet), which looked almost right and
 * behaved wrong in three ways a business would actually hit:
 *
 *   - It had no back button, only an "X". Every other pushed screen in
 *     this flow goes back with the chevron or the system gesture; this
 *     one silently didn't.
 *   - Android's hardware back closed the modal rather than navigating,
 *     so the two gestures disagreed about what "back" meant.
 *   - It could not carry a header of its own, so it showed the plain
 *     words "Order History" while the cart one tap behind it showed
 *     the supplier's avatar and name. Stepping from cart to history
 *     dropped the visual identity mid-flow -- exactly the problem the
 *     cart's own header was built to fix.
 *
 * As a route it inherits the stack's FeatureHeader, so all three go
 * away at once and the top bar can be the same social one used by the
 * catalogue, the product screen and the cart.
 *
 * THE ORDER DETAIL STAYS A SHEET. It is a peek at one row while
 * staying in the list -- genuinely modal, unlike this screen.
 */
export default function OrderHistoryScreen() {
  const { supplierId, supplierName: supplierNameParam } = useLocalSearchParams<{
    supplierId: string;
    supplierName?: string;
  }>();
  const navigation = useNavigation();
  const theme = useTheme();

  const { orders, isLoading, isError, refetch } = useOrderHistory(supplierId ?? "");
  // THE SCREEN THIS MATTERS MOST ON. Order history is opened exactly
  // when a business has NOTHING in their cart, so reading the supplier
  // off the cart -- which an earlier version did -- left this header
  // blank in its most common state: listing a supplier's orders
  // without naming the supplier. useSupplierIdentity falls through to
  // the profile when the cart cannot answer.
  const supplier = useSupplierIdentity(supplierId ?? "", supplierNameParam);

  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);

  const headerName = supplier.name;

  useLayoutEffect(() => {
    navigation.setOptions({
      ...(headerName
        ? {
            headerTitle: () => (
              <EntityHeaderTitle name={headerName} subtitle="Order history" photoUrl={supplier.photoUrl} />
            ),
          }
        : {}),
    });
  }, [navigation, headerName, supplier.photoUrl]);

  const renderItem = ({ item }: { item: OrderHistoryEntry }) => (
    <Pressable
      onPress={() => setSelectedOrderId(item.id)}
      style={[styles.row, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}
      accessibilityRole="button"
      accessibilityLabel={`Order ${item.orderReference} from ${formatDate(item.submittedAt)}`}
    >
      <View style={styles.rowHeader}>
        <Text style={[styles.reference, { color: theme.colors.onSurface }]}>{item.orderReference}</Text>
        <Text style={[styles.total, { color: theme.colors.onSurface }]}>{formatCents(item.totalCents)}</Text>
      </View>
      <Text style={[styles.date, { color: theme.colors.onSurfaceVariant }]}>{formatDate(item.submittedAt)}</Text>
      <Text style={[styles.detail, { color: theme.colors.onSurfaceVariant }]}>
        {item.itemCount} {item.itemCount === 1 ? "item" : "items"} ·{" "}
        {paymentMethodLabel(item.paymentMethod)} ·{" "}
        {item.deliveryType === "COLLECT" ? "Collect" : "Deliver"}
      </Text>
      <Text style={[styles.status, { color: theme.colors.primary }]}>{getStatusLabel(item.status)}</Text>
    </Pressable>
  );

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  // A MODAL COULD NOT DO THIS. The sheet had no error branch at all --
  // a failed request rendered the same "No past orders with this
  // supplier yet" as a genuinely empty history, telling a business
  // they had never ordered from someone they may well have.
  if (isError) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load your order history. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader paddingHorizontal={0}>
      {orders.length === 0 ? (
        <EmptyState
          icon={<Receipt size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
          message={
            headerName
              ? `You haven't placed an order with ${headerName} yet. Orders you submit appear here.`
              : "You haven't placed an order with this supplier yet. Orders you submit appear here."
          }
        />
      ) : (
        <FlatList
          data={orders}
          keyExtractor={(order) => order.id}
          contentContainerStyle={styles.list}
          renderItem={renderItem}
          showsVerticalScrollIndicator={false}
        />
      )}

      <OrderDetailSheet
        visible={selectedOrderId !== null}
        supplierId={supplierId ?? ""}
        orderId={selectedOrderId}
        onClose={() => setSelectedOrderId(null)}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  list: { padding: spacing.md, gap: spacing.sm },
  row: { borderWidth: 1, borderRadius: radius.lg, padding: spacing.md, gap: 2 },
  rowHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: spacing.sm },
  reference: { ...typography.body, fontWeight: "700", flexShrink: 1 },
  total: { ...typography.body, fontWeight: "800" },
  date: { ...typography.bodySmall },
  detail: { ...typography.bodySmall, fontSize: 12 },
  status: { ...typography.bodySmall, fontWeight: "700", marginTop: 2 },
});
