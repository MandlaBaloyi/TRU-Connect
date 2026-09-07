import React from "react";
import { FlatList, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { SupplierCatalogProductCard } from "./SupplierCatalogProductCard";
import type { SupplierProduct } from "../../find-supplier/types";

interface Props {
  supplierName: string;
  products: SupplierProduct[];
  onPressProduct: (product: SupplierProduct) => void;
  /** Same Add button the catalogue grid has. Omitted -> no button, so
   *  a context without a cart can still reuse this row. */
  onAddToCart?: (product: SupplierProduct) => void;
  addingProductId?: string | null;
}

const CARD_WIDTH = 160;

/**
 * "More from [Supplier]" -- reuses SupplierCatalogProductCard exactly
 * (same real card, same "% OFF" badge, same Out of Stock overlay),
 * just given a fixed pixel width instead of the grid's own percentage
 * width, since a horizontal scroll has no "column" to size against.
 *
 * "[Supplier Name]", not a generic "Related Products" -- honest about
 * what this actually is: not a recommendation engine, this supplier's
 * own other stock in the same category (backfilled with any other
 * product from this same supplier when fewer than 5 genuine matches
 * exist -- see the real backend's own list_related_products
 * docstring).
 *
 * NO ARROWS -- tried in an earlier pass, but they became a real
 * problem on their own: eating into the row's own width made it feel
 * MORE cramped, not more discoverable, the opposite of the intent.
 * Reverted to a plain scroll. Instead, contentInset-style padding on
 * the right lets the next card peek in slightly at the row's own
 * edge -- a lighter-weight "there's more here" cue that doesn't cost
 * any width.
 *
 * Renders nothing at all only when the supplier genuinely has no
 * other products at all.
 */
export function RelatedProductsRow({
  supplierName,
  products,
  onPressProduct,
  onAddToCart,
  addingProductId,
}: Props) {
  const theme = useTheme();

  if (products.length === 0) return null;

  return (
    <View style={styles.section}>
      <Text style={[styles.title, { color: theme.colors.onSurface }]}>More from {supplierName}</Text>
      <FlatList
        data={products}
        keyExtractor={(product) => product.id}
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <SupplierCatalogProductCard
            product={item}
            onPress={() => onPressProduct(item)}
            cardStyle={styles.card}
            onAddToCart={onAddToCart ? () => onAddToCart(item) : undefined}
            isAdding={addingProductId === item.id}
          />
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  section: { gap: spacing.sm },
  title: { ...typography.body, fontWeight: "700" },
  // paddingRight lets the last card's own edge sit short of the
  // screen edge -- the visual "more to see" cue.
  list: { gap: spacing.sm, paddingRight: spacing.lg },
  card: { width: CARD_WIDTH },
});
