import React, { useState } from "react";
import { ActivityIndicator, Alert, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useNavigation, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { ChevronUp, ShoppingCart } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { EmptyState } from "@/components/feedback/EmptyState";
import { ErrorState } from "@/components/feedback/ErrorState";
import { EntityHeaderTitle } from "@/components/navigation/EntityHeaderTitle";
import { orderHistoryHref, productDetailHref } from "../../routes";
import { formatCents } from "../../../supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useCart } from "../hooks/useCart";
import { useSupplierIdentity } from "../hooks/useSupplierIdentity";
import { useClearCart } from "../hooks/useClearCart";
import { CartItemRow } from "../components/CartItemRow";
import { CartMenu } from "../components/CartMenu";
import type { CartItem } from "../types";

/**
 * The real cart screen -- reached from the Stock Catalogue's own cart
 * icon. Scoped to exactly one supplier, matching how the backend's
 * own "one CART per (business, supplier) pair" guarantee works --
 * unlike the Bash reference, there's no "Sold by" repeated per row,
 * since the supplier's name is already the one thing this whole
 * screen is about; it's shown once, prominently, at the top instead.
 */
export default function CartScreen() {
  const { supplierId } = useLocalSearchParams<{ supplierId: string }>();
  const navigation = useNavigation();
  const router = useRouter();
  const theme = useTheme();
  const { cart, isLoading, isError, refetch, updateQuantity, removeItem, isUpdatingQuantity, isRemoving } = useCart(
    supplierId ?? ""
  );
  const { clearCart, isClearing } = useClearCart(supplierId ?? "");
  // Not `cart?.supplierName`: an EMPTY cart is null, and the header
  // still has to say whose cart it is. See useSupplierIdentity.
  const supplier = useSupplierIdentity(supplierId ?? "");

  const [summaryExpanded, setSummaryExpanded] = useState(false);
  const [scrollY, setScrollY] = useState(0);
  const [itemCountY, setItemCountY] = useState<number | null>(null);
  const isItemCountSticky = itemCountY !== null && scrollY >= itemCountY;

  const handleClearCart = () => {
    Alert.alert("Clear cart?", "This removes every item in your cart. This can't be undone.", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Clear cart",
        style: "destructive",
        onPress: () => {
          clearCart().catch(() => Alert.alert("Couldn't clear cart", "Check your connection and try again."));
        },
      },
    ]);
  };

  React.useLayoutEffect(() => {
    navigation.setOptions({
      title: supplier.name ?? "Cart",
      // Same social top bar as the catalogue this screen is reached
      // from -- the supplier's avatar + name, with "Cart" as the quiet
      // second line. Without the avatar, stepping catalogue -> cart
      // dropped the visual identity mid-flow and the header became a
      // bare name again.
      ...(supplier.name
        ? {
            headerTitle: () => (
              <EntityHeaderTitle name={supplier.name!} subtitle="Cart" photoUrl={supplier.photoUrl} />
            ),
          }
        : {}),
      headerRight: () => (
        <CartMenu
          // PUSHES A SCREEN now, rather than opening a full-screen
          // modal -- see OrderHistoryScreen's own docstring for the
          // three things the modal got wrong. The supplier's name goes
          // with it so that screen's header is right on its first
          // frame; this screen already has it.
          onOrderHistory={() => router.push(orderHistoryHref(supplierId ?? "", supplier.name) as any)}
          onClearCart={handleClearCart}
        />
      ),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigation, supplier.name, supplier.photoUrl]);

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load your cart. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  if (!cart || !cart.items?.length) {
    return (
      <ScreenContainer hasNativeHeader>
        <EmptyState
          icon={<ShoppingCart size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
          message="Your cart is empty. Add products from this supplier's Stock Catalogue to get started."
        />
      </ScreenContainer>
    );
  }

  const hasStaleItems = cart.items.some((item) => item.isStale);

  const handleIncrement = (item: CartItem) => updateQuantity({ productId: item.productId, quantity: item.quantity + 1 });
  const handleDecrement = (item: CartItem) => updateQuantity({ productId: item.productId, quantity: item.quantity - 1 });

  return (
    <ScreenContainer hasNativeHeader>
      {isItemCountSticky && (
        <View style={[styles.stickyBadge, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
          <Text style={[styles.stickyBadgeText, { color: theme.colors.onSurface }]}>
            {cart.itemCount} {cart.itemCount === 1 ? "item" : "items"}
          </Text>
        </View>
      )}
      <FlatList
        data={cart.items}
        keyExtractor={(item) => item.productId}
        contentContainerStyle={styles.list}
        onScroll={(event) => setScrollY(event.nativeEvent.contentOffset.y)}
        scrollEventThrottle={16}
        ListHeaderComponent={
          <View
            onLayout={(event) =>
              setItemCountY(event.nativeEvent.layout.y + event.nativeEvent.layout.height)
            }
          >
            <Text style={[styles.itemCount, { color: theme.colors.onSurfaceVariant }]}>
              {cart.itemCount} {cart.itemCount === 1 ? "item" : "items"}
            </Text>
          </View>
        }
        ItemSeparatorComponent={() => <View style={[styles.separator, { backgroundColor: theme.colors.outlineVariant }]} />}
        renderItem={({ item }) => (
          <CartItemRow
            item={item}
            onPress={() => router.push(productDetailHref(supplierId, item.productId, item.productName, cart.supplierName) as any)}
            onIncrement={() => handleIncrement(item)}
            onDecrement={() => handleDecrement(item)}
            onRemove={() => removeItem(item.productId)}
            isBusy={isUpdatingQuantity || isRemoving}
          />
        )}
      />

      <View style={[styles.summaryBar, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
        <Pressable
          onPress={() => setSummaryExpanded((prev) => !prev)}
          style={styles.summaryHeader}
          accessibilityRole="button"
          accessibilityLabel="Order summary"
        >
          <Text style={[styles.summaryLabel, { color: theme.colors.onSurface }]}>
            Order summary • {cart.itemCount} {cart.itemCount === 1 ? "item" : "items"}
          </Text>
          <ChevronUp
            size={18}
            color={theme.colors.onSurfaceVariant}
            strokeWidth={2}
            style={{ transform: [{ rotate: summaryExpanded ? "0deg" : "180deg" }] }}
          />
        </Pressable>
        {summaryExpanded && (
          <View style={styles.summaryDetail}>
            {cart.items.map((item) => (
              <View key={item.productId} style={styles.summaryRow}>
                <Text style={[styles.summaryItemLabel, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
                  {item.quantity} × {item.productName}
                </Text>
                <Text style={[styles.summaryItemValue, { color: theme.colors.onSurface }]}>
                  {formatCents(item.lineTotalCents)}
                </Text>
              </View>
            ))}
          </View>
        )}
      </View>

      <View style={[styles.bottomBar, { backgroundColor: theme.colors.surface, borderTopColor: theme.colors.outlineVariant }]}>
        <View>
          <Text style={[styles.bottomBarLabel, { color: theme.colors.onSurfaceVariant }]}>Total</Text>
          <Text style={[styles.bottomBarTotal, { color: theme.colors.onSurface }]}>{formatCents(cart.totalCents)}</Text>
        </View>
        <Pressable
          onPress={() => router.push(`/business/orders/${supplierId}/delivery-payment` as any)}
          disabled={hasStaleItems}
          style={[styles.checkoutButton, { backgroundColor: theme.colors.primary }, hasStaleItems && styles.checkoutButtonDisabled]}
          accessibilityRole="button"
          accessibilityLabel="Checkout"
        >
          <Text style={[styles.checkoutLabel, { color: theme.colors.onPrimary }]}>Checkout</Text>
        </Pressable>
      </View>

    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  stickyBadge: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    zIndex: 10,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  stickyBadgeText: { ...typography.bodySmall, fontWeight: "700" },
  list: { padding: spacing.md, paddingBottom: 180 },
  itemCount: { ...typography.bodySmall, marginBottom: spacing.sm },
  separator: { height: StyleSheet.hairlineWidth },
  summaryBar: { position: "absolute", bottom: 80, left: 0, right: 0, borderTopWidth: StyleSheet.hairlineWidth, paddingHorizontal: spacing.md },
  summaryHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingVertical: spacing.sm },
  summaryLabel: { ...typography.body, fontWeight: "700" },
  summaryDetail: { paddingBottom: spacing.sm, gap: 4 },
  summaryRow: { flexDirection: "row", justifyContent: "space-between", gap: spacing.sm },
  summaryItemLabel: { ...typography.bodySmall, flex: 1 },
  summaryItemValue: { ...typography.bodySmall, fontWeight: "600" },
  bottomBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  bottomBarLabel: { ...typography.caption },
  bottomBarTotal: { ...typography.h2, fontWeight: "700" },
  checkoutButton: { minWidth: 140, minHeight: 48, borderRadius: radius.md, alignItems: "center", justifyContent: "center" },
  checkoutButtonDisabled: { opacity: 0.5 },
  checkoutLabel: { fontWeight: "700", fontSize: 16 },
});
