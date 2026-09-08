import React from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Package, Plus } from "lucide-react-native";

import { calculateDiscount } from "../../../../supplier/products/algorithms/discount";
import { formatCents } from "../../../../supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { SupplierProduct } from "../../types";

export const SALE_CARD_WIDTH = 164;

/**
 * A product in the "On sale" strip.
 *
 * THE SAVING IS THE HEADLINE, not the name. On every other card the
 * product is what you are reading and the price is confirmation; here
 * it is the other way round -- the section exists because the price
 * changed, so the discount takes the top-left corner and the old price
 * sits struck through beside the new one.
 *
 * A CORNER RIBBON RATHER THAN A PILL, and it is the one place in the
 * app that uses one. That is deliberate: a sale strip has to be
 * distinguishable from the strips above and below it at a glance,
 * while scrolling, without reading a heading. If every section used
 * the same rounded badge in the same corner, the sections would be
 * different lists of the same card -- which is exactly the problem
 * this whole storefront exists to fix.
 *
 * NO ACTIONS ROW, unlike the category strips below. The heart /
 * comment / share icons stay on those cards, where the strip is a
 * catalogue and a business is browsing; here they were three taps
 * nobody takes eating the vertical space the PHOTO wants. A
 * merchandised card has one job -- make the product legible enough to
 * be chosen -- and the image is what does that job.
 */
export function SaleProductCard({
  product,
  onPress,
  onAddToCart,
  isAdding = false,
}: {
  product: SupplierProduct;
  onPress: () => void;
  onAddToCart?: () => void;
  isAdding?: boolean;
}) {
  const theme = useTheme();
  const discount = calculateDiscount(product.priceCents, product.compareAtPriceCents);
  const photo = product.images[0] ?? null;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        { borderColor: theme.colors.outlineVariant, backgroundColor: theme.colors.surface },
        pressed && { opacity: 0.85 },
      ]}
      accessibilityRole="button"
      accessibilityLabel={`${product.name}, on sale, ${formatCents(product.priceCents)}`}
    >
      <View style={[styles.imageWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
        {photo ? (
          <Image source={{ uri: photo }} style={styles.image} resizeMode="contain" />
        ) : (
          <Package size={26} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />
        )}

        {discount && (
          <View style={[styles.ribbon, { backgroundColor: theme.colors.error }]}>
            <Text style={styles.ribbonText}>{discount.percentOff}% OFF</Text>
          </View>
        )}

        {!product.inStock && (
          <View style={styles.outOfStock}>
            <Text style={styles.outOfStockText}>OUT OF STOCK</Text>
          </View>
        )}
      </View>

      <View style={styles.body}>
        <View style={styles.priceRow}>
          <Text style={[styles.price, { color: theme.colors.error }]}>
            {formatCents(product.priceCents)}
          </Text>
          {product.compareAtPriceCents !== null && (
            <Text style={[styles.was, { color: theme.colors.onSurfaceVariant }]}>
              {formatCents(product.compareAtPriceCents)}
            </Text>
          )}
        </View>
        <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={2}>
          {product.name}
        </Text>

        {onAddToCart && (
          <Pressable
            onPress={(event) => {
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

      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { width: SALE_CARD_WIDTH, borderWidth: 1, borderRadius: radius.md, overflow: "hidden" },
  imageWrap: { width: "100%", aspectRatio: 1, alignItems: "center", justifyContent: "center" },
  image: { width: "100%", height: "100%" },
  ribbon: {
    position: "absolute",
    top: 0,
    left: 0,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    borderBottomRightRadius: radius.md,
  },
  ribbonText: { color: "#FFFFFF", fontSize: 11, fontWeight: "800", letterSpacing: 0.3 },
  outOfStock: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0,0,0,0.45)",
    alignItems: "center",
    justifyContent: "center",
  },
  outOfStockText: { color: "#FFFFFF", fontSize: 11, fontWeight: "700", letterSpacing: 0.5 },
  body: { padding: spacing.sm, gap: 2 },
  priceRow: { flexDirection: "row", alignItems: "baseline", gap: 6, flexWrap: "wrap" },
  price: { ...typography.body, fontWeight: "800" },
  was: { ...typography.bodySmall, fontSize: 12, textDecorationLine: "line-through" },
  name: { ...typography.bodySmall, fontSize: 12, lineHeight: 16 },
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
});
