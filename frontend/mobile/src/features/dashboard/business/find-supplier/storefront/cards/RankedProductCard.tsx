import React from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Package } from "lucide-react-native";

import { describeUnit } from "@/components/products/unitEconomics";
import { formatCents } from "../../../../supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { SupplierProduct } from "../../types";

export const RANKED_CARD_WIDTH = 150;

/**
 * A product in "What businesses buy most", carrying its position.
 *
 * THE RANK IS THE WHOLE POINT. "Everyone buys this" is a completely
 * different claim from "this is cheap", and a numeral says it in a way
 * no badge can: #1 is only meaningful because #2 and #3 are beside it.
 * A list is the format the claim needs.
 *
 * THE NUMERAL OVERLAPS THE IMAGE CORNER rather than sitting in a
 * caption. It has to be readable while scrolling past, and it is the
 * only element on this card competing with the photo for attention --
 * which is correct, because it is the reason the section exists.
 *
 * ONLY THE TOP FEW ARE WORTH RANKING. Beyond three or four, a
 * position stops being a recommendation and starts being trivia --
 * StorefrontSectionView caps what it hands over here.
 *
 * NO DISCOUNT BADGE, even when the product is on sale. It might well
 * be, but this section is answering popularity; adding a second claim
 * to the same card muddies both, and the sale strip above already
 * makes that argument properly.
 *
 * NO ACTIONS ROW, unlike the category strips below. The heart /
 * comment / share icons stay on those cards, where the strip is a
 * catalogue and a business is browsing; here they were three taps
 * nobody takes eating the vertical space the PHOTO wants. A
 * merchandised card has one job -- make the product legible enough to
 * be chosen -- and the image is what does that job.
 */
export function RankedProductCard({
  product,
  rank,
  onPress,
}: {
  product: SupplierProduct;
  rank: number;
  onPress: () => void;
}) {
  const theme = useTheme();
  const photo = product.images[0] ?? null;
  const unit = describeUnit(product.sellingUnit, product.unitQuantity, product.unitMeasure);

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && { opacity: 0.85 }]}
      accessibilityRole="button"
      accessibilityLabel={`Number ${rank}, ${product.name}, ${formatCents(product.priceCents)}`}
    >
      <View style={[styles.imageWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
        {photo ? (
          <Image source={{ uri: photo }} style={styles.image} resizeMode="contain" />
        ) : (
          <Package size={26} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />
        )}

        {!product.inStock && (
          <View style={styles.outOfStock}>
            <Text style={styles.outOfStockText}>OUT OF STOCK</Text>
          </View>
        )}
      </View>

      {/* Outside the image wrapper so it is never dimmed by the
          out-of-stock scrim -- a product's popularity is still true
          while it is unavailable. */}
      <View style={[styles.rankBadge, { backgroundColor: theme.colors.onSurface }]}>
        <Text style={[styles.rankText, { color: theme.colors.surface }]}>{rank}</Text>
      </View>

      <View style={styles.body}>
        <Text style={[styles.price, { color: theme.colors.onSurface }]}>
          {formatCents(product.priceCents)}
        </Text>
        <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={2}>
          {product.name}
        </Text>
        {unit && (
          <Text style={[styles.unit, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
            {unit}
          </Text>
        )}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { width: RANKED_CARD_WIDTH },
  imageWrap: {
    width: "100%",
    aspectRatio: 1,
    borderRadius: radius.md,
    overflow: "hidden",
    alignItems: "center",
    justifyContent: "center",
  },
  image: { width: "100%", height: "100%" },
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
  outOfStockText: { color: "#FFFFFF", fontSize: 10, fontWeight: "700", letterSpacing: 0.5 },
  rankBadge: {
    position: "absolute",
    top: -6,
    left: -6,
    minWidth: 30,
    height: 30,
    borderRadius: 15,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 6,
  },
  rankText: { ...typography.body, fontWeight: "800", fontSize: 15 },
  body: { paddingTop: spacing.sm, gap: 1 },
  price: { ...typography.body, fontWeight: "800" },
  name: { ...typography.bodySmall, fontSize: 12, lineHeight: 16 },
  unit: { ...typography.caption, fontSize: 11 },
});
