import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { ShoppingCart } from "lucide-react-native";

import { useCart } from "@/features/dashboard/business/orders/hooks/useCart";
import { spacing } from "@/theme/spacing";

/**
 * The cart, with its live count, for a Community screen's header.
 *
 * EXTRACTED FROM SupplierCatalogScreen, which built this inline. It
 * was the only screen with a cart button, which was itself the
 * problem: a business reading a supplier's profile or a single product
 * had no way to see that they already had six items waiting, and no
 * way to reach them without going back. The cart belongs on every
 * screen where you can add to it.
 *
 * READS THE CART ITSELF rather than taking a count as a prop. Every
 * screen that shows this already calls useCart for the same supplier,
 * so this shares that exact query -- same key, deduped by React Query,
 * no extra request -- and no screen has to remember to thread a number
 * through its header options.
 *
 * HIDDEN WHEN EMPTY, deliberately. An empty cart icon is a button that
 * leads to an empty screen; on a narrow phone header that space is
 * better given to the supplier's name. It appears the moment there is
 * something in it, which is also the moment it becomes worth noticing.
 */
export function CartButton({ supplierId }: { supplierId: string }) {
  const theme = useTheme();
  const router = useRouter();
  const { cart } = useCart(supplierId);

  const count = cart?.itemCount ?? 0;
  if (count === 0) return null;

  return (
    <Pressable
      onPress={() => router.push(`/business/orders/${supplierId}` as any)}
      hitSlop={8}
      style={styles.button}
      accessibilityRole="button"
      accessibilityLabel={`Cart, ${count} ${count === 1 ? "item" : "items"}`}
    >
      <ShoppingCart size={20} color={theme.colors.onSurface} strokeWidth={2.2} />
      <View style={[styles.badge, { backgroundColor: theme.colors.error }]}>
        <Text style={styles.badgeText}>{count > 9 ? "9+" : count}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: { padding: spacing.xs, position: "relative" },
  badge: {
    position: "absolute",
    top: 0,
    right: 0,
    minWidth: 16,
    height: 16,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 3,
  },
  badgeText: { color: "#FFFFFF", fontSize: 10, fontWeight: "700" },
});
