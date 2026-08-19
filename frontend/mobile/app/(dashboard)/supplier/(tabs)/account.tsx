import React from "react";
import { View, StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";
import { FeatureTile } from "@/components/cards/FeatureTile";
import { ProductsIcon } from "@/features/dashboard/supplier/products/components/ProductsIcon";
import { InventoryIcon } from "@/features/dashboard/supplier/inventory/components/InventoryIcon";
import { spacing } from "@/theme/spacing";

/** Supplier Account tab — same architecture as Business's Account
 *  (contextual header + tile grid). Phase 1 supplier tools per the
 *  approved plan: Products and Inventory now, Orders next.
 *
 *  INVENTORY IS ITS OWN TILE, NOT INSIDE PRODUCTS, per direct
 *  instruction -- "what do I sell" (Products) and "how much of it do
 *  I have" (Inventory) are different questions, same reasoning that
 *  already keeps Bulk Products' actual routes separate from Products'
 *  own even though Products links to them.
 *
 *  NO SEPARATE "BULK PRODUCTS" TILE -- per review, it was removed once
 *  Bulk Upload/Bulk Edit became directly reachable from inside
 *  Products itself (the shortcut pills + the "⋮" header menu). The
 *  bulk-products feature folder and its routes (edit/import screens)
 *  are unchanged and fully functional; only this standalone entry
 *  point and its own home screen (BulkProductsHomeScreen, now genuinely
 *  unreachable and removed) went away, since Products already covers
 *  both destinations that home screen used to offer. */
export default function SupplierAccount() {
  const router = useRouter();

  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      <AppHeader variant="title" title="Account" subtitle="Your business tools" />
      <View style={styles.grid}>
        <View style={styles.tileWrapper}>
          <FeatureTile
            label="Products"
            icon={<ProductsIcon size={40} />}
            onPress={() => router.push("/supplier/products")}
          />
        </View>

        <View style={styles.tileWrapper}>
          <FeatureTile
            label="Inventory"
            icon={<InventoryIcon size={40} />}
            onPress={() => router.push("/supplier/inventory")}
          />
        </View>

        {/* Orders tile goes here next */}
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
    padding: spacing.md,
  },
  tileWrapper: {
    width: "31%",
  },
});
