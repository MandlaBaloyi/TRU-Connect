import React from "react";
import { View, StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { MoreVertical } from "lucide-react-native";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";
import { FeatureTile } from "@/components/cards/FeatureTile";
import { ProductsIcon } from "@/features/dashboard/supplier/products/components/ProductsIcon";
import { InventoryIcon } from "@/features/dashboard/supplier/inventory/components/InventoryIcon";
import { StockOrdersIcon } from "@/features/dashboard/supplier/stock-orders/components/StockOrdersIcon";
import { spacing } from "@/theme/spacing";
import { useGridColumnWidth } from "@/hooks/useGridColumnWidth";

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
 *  both destinations that home screen used to offer.
 *
 *  THE 3-DOT MENU -- a real, confirmed asymmetry found and fixed: the
 *  business side's own Account tab already had one; this side never
 *  did. Added now, unwired (matches Loan Book/Order Book's own
 *  "visible now, real menu decided and wired later" placeholder
 *  discipline), rather than silently left missing. */
export default function SupplierAccount() {
  const router = useRouter();
  const theme = useTheme();
  // THE REAL FIX for a genuine, confirmed bug -- see
  // useGridColumnWidth's own docstring. A real screenshot showed
  // exactly 2 tiles per row instead of the intended 3, on a grid
  // using percentage widths that never accounted for the real gap
  // between them. 3 columns, matching the "5-9 core features" scale
  // this grid needs to support going forward.
  const tileWidth = useGridColumnWidth(3, spacing.md, spacing.md);

  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      <AppHeader
        variant="title"
        title="Account"
        subtitle="Your business tools"
        rightIcon={<MoreVertical size={20} color={theme.colors.onSurface} strokeWidth={2.4} />}
      />
      <View style={styles.grid}>
        <View style={{ width: tileWidth }}>
          <FeatureTile
            label="Products"
            icon={<ProductsIcon size={40} />}
            onPress={() => router.push("/supplier/products")}
          />
        </View>

        <View style={{ width: tileWidth }}>
          <FeatureTile
            label="Inventory"
            icon={<InventoryIcon size={40} />}
            onPress={() => router.push("/supplier/inventory")}
          />
        </View>

        <View style={{ width: tileWidth }}>
          <FeatureTile
            label="Stock Orders"
            icon={<StockOrdersIcon size={40} />}
            onPress={() => router.push("/supplier/stock-orders" as any)}
          />
        </View>
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
});
