import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { CategoryImage } from "@/components/categories";
import { useTheme } from "react-native-paper";
import { Plus } from "lucide-react-native";

import { ProductActionsRow } from "@/components/products/ProductActionsRow";
import { calculateDiscount } from "../../../supplier/products/algorithms/discount";
import { sellingUnitLabel } from "@/components/products/sellingUnitLabel";
import { formatCents } from "../../../supplier/products/services/productMapper";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { SupplierProduct } from "../../find-supplier/types";

interface Props {
  product: SupplierProduct;
  onPress: () => void;
  /** Omitted -> no Add button at all. Kept optional so a context
   *  without a cart (a future preview, a supplier's own view) can reuse
   *  this card without pretending to offer ordering. */
  onAddToCart?: () => void;
  isAdding?: boolean;
  /** Optional override for the card's own outer width -- the default
   *  (48%) only makes sense inside the 2-column grid this card was
   *  built for. "More from [Supplier]" reuses this exact same card in
   *  a horizontal scroll instead, where a percentage width doesn't
   *  apply; that section passes a fixed pixel width here rather than
   *  this file needing a second, near-duplicate card component. */
  cardStyle?: object;
}

/**
 * A photo-forward grid card -- reusing calculateDiscount/formatCents
 * directly from the supplier's own products feature rather than
 * re-deriving the same formula a second time.
 *
 * "contain", NOT "cover" -- the whole product shows, every time, on a
 * plain neutral background, matching real marketplaces (Amazon,
 * Temu) serving many different sellers with many different kinds of
 * product photography.
 *
 * NO CATEGORY TEXT HERE -- removed after direct feedback: this screen
 * exists to tell an informal business what's actually available, and
 * a category label under every single card was noise against that
 * goal, not useful information at a glance. Name, price, stock status,
 * and the three action icons are what's left -- everything that
 * actually helps someone decide whether to look closer.
 *
 * OUT OF STOCK -- a real, direct visual state, not just implied by
 * missing data. A dimmed image plus a clear label, same convention
 * real e-commerce apps use: still fully viewable (there's real value
 * in seeing what a supplier carries even when it's temporarily
 * unavailable), just visually distinct from something orderable.
 *
 * THREE ACTION ICONS (heart, comment, share) -- bigger and bolder
 * after direct feedback (20px, heavier stroke, up from a size that
 * read as an afterthought against the rest of the card). Still UI
 * only -- each shows a real "Coming soon" alert on tap. Each is its
 * own Pressable nested inside the card's own outer one; React Native
 * isolates touch handling per-Pressable, so tapping an icon fires
 * only that icon's own handler, never also navigating to the product
 * detail screen the outer Pressable leads to.
 *
 * 2-up grid (see SupplierCatalogScreen.tsx's own layout).
 */
export function SupplierCatalogProductCard({ product, onPress, cardStyle, onAddToCart, isAdding = false }: Props) {
  const theme = useTheme();
  const discount = calculateDiscount(product.priceCents, product.compareAtPriceCents);
  const photoUrl = product.images[0] ?? null;
  const unitLabel = sellingUnitLabel(product.sellingUnit, product.unitQuantity, product.unitMeasure);

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        cardStyle,
        { borderColor: theme.colors.outlineVariant, backgroundColor: theme.colors.surface },
        pressed && styles.cardPressed,
      ]}
      accessibilityRole="button"
      accessibilityLabel={`View ${product.name}`}
    >
      <View style={[styles.imageWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
        {/* See ProductCard -- one chain, one behaviour: photo, then the
            category tile, then neutral, with a dead URL falling through
            rather than rendering an empty box. */}
        <CategoryImage photoUrl={photoUrl} category={product.category} fill resizeMode="contain" />
        {discount && (
          <View style={[styles.discountBadge, { backgroundColor: theme.colors.error }]}>
            <Text style={styles.discountBadgeText}>{discount.percentOff}% OFF</Text>
          </View>
        )}
        {!product.inStock && (
          <View style={styles.outOfStockOverlay}>
            <View style={styles.outOfStockBadge}>
              <Text style={styles.outOfStockText}>OUT OF STOCK</Text>
            </View>
          </View>
        )}
      </View>

      <View style={styles.body}>
        <Text
          style={[styles.name, { color: theme.colors.onSurface }]}
          numberOfLines={2}
        >
          {product.name}
        </Text>

        <View style={styles.priceRow}>
          <Text style={[styles.price, { color: theme.colors.onSurface }]}>
            {formatCents(product.priceCents)}
          </Text>
          {discount && product.compareAtPriceCents !== null && (
            <Text style={[styles.compareAtPrice, { color: theme.colors.onSurfaceVariant }]}>
              {formatCents(product.compareAtPriceCents)}
            </Text>
          )}
        </View>
        {/* The unit the price is quoted in -- see sellingUnitLabel on
            why a bare price is unusable for a wholesale decision. */}
        {unitLabel && (
          <Text style={[styles.unitLabel, { color: theme.colors.onSurfaceVariant }]}>{unitLabel}</Text>
        )}

        {/* ADD STRAIGHT FROM THE GRID. The reason this exists: a spaza
            owner restocking buys the same fifteen known lines every
            week, and making them open fifteen product pages to add
            fifteen things was the single biggest friction in the app.
            Consumer retail can afford a product page per item; wholesale
            reordering cannot.

            Out of stock keeps the row but disables it, rather than
            hiding it -- a missing button reads as a broken card, where a
            greyed one reads as "not right now". */}
        {onAddToCart && (
          <Pressable
            onPress={(event) => {
              // The whole card navigates; this must not.
              event.stopPropagation();
              onAddToCart();
            }}
            disabled={!product.inStock || isAdding}
            style={({ pressed }) => [
              styles.addButton,
              {
                backgroundColor: product.inStock ? theme.colors.primary : theme.colors.surfaceVariant,
                opacity: !product.inStock || isAdding ? 0.5 : pressed ? 0.85 : 1,
              },
            ]}
            accessibilityRole="button"
            accessibilityLabel={product.inStock ? `Add ${product.name} to cart` : `${product.name} is out of stock`}
            accessibilityState={{ disabled: !product.inStock || isAdding }}
          >
            <Plus
              size={15}
              color={product.inStock ? theme.colors.onPrimary : theme.colors.onSurfaceVariant}
              strokeWidth={2.6}
            />
            <Text
              style={[
                styles.addLabel,
                { color: product.inStock ? theme.colors.onPrimary : theme.colors.onSurfaceVariant },
              ]}
            >
              {isAdding ? "Adding…" : product.inStock ? "Add" : "Out of stock"}
            </Text>
          </Pressable>
        )}

        <ProductActionsRow productName={product.name} />
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  addButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    minHeight: 34,
    borderRadius: radius.md,
    marginTop: spacing.xs,
  },
  addLabel: { ...typography.bodySmall, fontWeight: "700" },
  unitLabel: { ...typography.bodySmall, fontSize: 11, marginTop: 1 },
  card: {
    width: "48%",
    borderWidth: 1,
    borderRadius: radius.md,
    overflow: "hidden",
  },
  cardPressed: { opacity: 0.85 },
  imageWrap: {
    width: "100%",
    aspectRatio: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  discountBadge: { position: "absolute", top: spacing.xs, left: spacing.xs, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 3 },
  discountBadgeText: { color: "#FFFFFF", fontSize: 10, fontWeight: "700" },
  outOfStockOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0,0,0,0.45)",
    alignItems: "center",
    justifyContent: "center",
  },
  outOfStockBadge: { backgroundColor: "rgba(0,0,0,0.75)", paddingHorizontal: 10, paddingVertical: 5, borderRadius: 4 },
  outOfStockText: { color: "#FFFFFF", fontSize: 11, fontWeight: "700", letterSpacing: 0.5 },
  body: { padding: spacing.sm, gap: 2 },
  name: { ...typography.body, fontWeight: "700" },
  priceRow: { flexDirection: "row", alignItems: "center", flexWrap: "wrap", gap: 6, marginTop: 2 },
  price: { ...typography.body, fontWeight: "700" },
  compareAtPrice: { ...typography.bodySmall, textDecorationLine: "line-through" },
});
