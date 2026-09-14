import React from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { ImageOff } from "lucide-react-native";

import { formatCents } from "@/features/dashboard/supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { FeedProduct } from "../../types";

export const PRODUCT_TILE_WIDTH = 148;

/**
 * A product, as a tile in a rail.
 *
 * THE SUPPLIER'S NAME IS ON EVERY TILE, and that is the difference
 * between this and the food-delivery apps it borrows its shape from.
 * There, a card's shop is implied by the section you are in. Here a
 * single rail deliberately mixes suppliers -- "Buy it again" spans
 * everyone a business orders from -- so a price with no supplier
 * attached is unusable: it is a different minimum order, a different
 * delivery arrangement, and a different cart.
 *
 * NO ADD-TO-CART BUTTON ON THE TILE, deliberately. Adding requires a
 * quantity, an active connection, and a supplier's minimum-order
 * terms that only make sense on the product screen. A one-tap add
 * that can fail four different ways is a worse experience than a tap
 * that opens the product -- and it is the product screen where the
 * business finds out what they are actually committing to.
 *
 * "4 BUSINESSES BOUGHT THIS" IS THE ONLY LINE HERE THAT IS NOBODY'S
 * OPINION. The price is the supplier's, the ordering is ours; this is
 * what other shops actually did. The SENTENCE is built server-side
 * (shared/algorithms/social_proof.py) so the feed and the catalogue
 * browse cannot word it differently, and it is absent rather than zero
 * when nobody has bought the product -- a "0 businesses" badge is true
 * and reads as a warning.
 *
 * DISCOUNTS SHOW THE SAVING, NOT THE PERCENTAGE. Direct feedback on
 * the product screen: "rather than saying you save R50, says save
 * R50". The same wording is used here.
 */
export function ProductTile({
  product,
  onPress,
  width = PRODUCT_TILE_WIDTH,
}: {
  product: FeedProduct;
  onPress: () => void;
  width?: number;
}) {
  const theme = useTheme();
  const savingCents =
    product.compareAtPriceCents !== null && product.compareAtPriceCents > product.priceCents
      ? product.compareAtPriceCents - product.priceCents
      : null;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.tile, { width, opacity: pressed ? 0.85 : 1 }]}
      accessibilityRole="button"
      accessibilityLabel={[
        product.name,
        `from ${product.supplierName}`,
        formatCents(product.priceCents),
        // Social proof belongs in the spoken label too -- it is a
        // reason to tap, and a screen reader user gets the same
        // reasons a sighted one does.
        product.buyerLabel,
      ]
        .filter(Boolean)
        .join(", ")}
    >
      <View style={[styles.imageWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
        {product.imageUrl ? (
          <Image source={{ uri: product.imageUrl }} style={styles.image} resizeMode="cover" />
        ) : (
          // A DESIGNED EMPTY, not a broken one. Plenty of real
          // products in this catalogue have no photo -- a supplier
          // adding stock from a phone in a yard does not always stop
          // to take one -- so this state has to look intentional.
          <ImageOff size={22} color={theme.colors.onSurfaceVariant} strokeWidth={1.6} />
        )}

        {savingCents !== null && (
          <View style={[styles.savingPill, { backgroundColor: theme.colors.primary }]}>
            <Text style={[styles.savingText, { color: theme.colors.onPrimary }]}>
              Save {formatCents(savingCents)}
            </Text>
          </View>
        )}

        {!product.inStock && (
          <View style={styles.stockScrim}>
            <Text style={styles.stockScrimText}>Out of stock</Text>
          </View>
        )}
      </View>

      <View style={styles.body}>
        <Text style={[styles.price, { color: theme.colors.onSurface }]}>
          {formatCents(product.priceCents)}
        </Text>
        <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={2}>
          {product.name}
        </Text>
        <Text style={[styles.supplier, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
          {product.unitLabel ? `${product.unitLabel} · ` : ""}
          {product.supplierName}
        </Text>
        {product.buyerLabel ? (
          <Text style={[styles.buyers, { color: theme.colors.primary }]} numberOfLines={1}>
            {product.buyerLabel}
          </Text>
        ) : null}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  tile: { gap: spacing.sm },
  imageWrap: {
    height: 120,
    borderRadius: radius.md,
    overflow: "hidden",
    alignItems: "center",
    justifyContent: "center",
  },
  image: { width: "100%", height: "100%" },
  savingPill: {
    position: "absolute",
    top: spacing.xs,
    left: spacing.xs,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.pill,
  },
  savingText: { ...typography.caption, fontWeight: "800", fontSize: 10 },
  // The four edges written out rather than spreading
  // StyleSheet.absoluteFill: that constant is a REGISTERED STYLE ID,
  // not a plain object, so spreading it yields {} and the scrim
  // silently disappears -- a bug the type checker is happy with.
  // (absoluteFillObject is the object form, but it is missing from
  // this project's RN typings.)
  stockScrim: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0,0,0,0.55)",
    alignItems: "center",
    justifyContent: "center",
  },
  stockScrimText: { ...typography.caption, fontWeight: "800", color: "#fff" },
  body: { gap: 1 },
  price: { ...typography.body, fontWeight: "800" },
  name: { ...typography.bodySmall, fontSize: 12, lineHeight: 16 },
  supplier: { ...typography.caption, fontSize: 11 },
  // Tinted rather than grey: this is the one line on the tile meant to
  // be a REASON, not a detail. One line only -- a tile is 148px wide
  // and a wrapped badge would push every tile in the rail to a
  // different height.
  buyers: { ...typography.caption, fontSize: 10, fontWeight: "700" },
});
