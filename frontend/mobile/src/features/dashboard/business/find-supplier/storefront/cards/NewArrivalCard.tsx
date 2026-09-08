import React from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Package } from "lucide-react-native";

import { describeUnit } from "@/components/products/unitEconomics";
import { formatCents } from "../../../../supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { SupplierProduct } from "../../types";

export const NEW_ARRIVAL_CARD_WIDTH = 156;

/**
 * A product in "Just added", and in the supplier's own curated strips.
 *
 * THE QUESTION IT ANSWERS is the one a repeat buyer actually arrives
 * with. Someone restocking already knows the fifteen lines they buy
 * every week -- what they cannot know without scrolling the entire
 * catalogue is what has CHANGED since last time. That is a different
 * job from "what is cheap" or "what is popular", so it gets its own
 * strip rather than a badge on an existing one.
 *
 * THE BIGGEST PHOTO OF ANY CARD HERE, deliberately. A new product has
 * no track record, no rank and no discount to argue with -- the
 * picture is the entire pitch, so it gets a taller frame and the flag
 * is the only thing overlapping it.
 *
 * NO ADD BUTTON. Something a business has never seen before is
 * precisely what they should open and read rather than add blind --
 * the unit, the pack size and the description are the whole point of
 * a first look. The strips whose products a buyer already knows keep
 * their Add.
 *
 * ALSO SERVES CURATED STRIPS, without the flag. A supplier's own
 * "Stock up for month-end" selection has the same shape of need --
 * image-forward, nothing to rank it by -- and giving it a second
 * near-identical card would be exactly the duplication the Community
 * feed already had to unpick once.
 */
export function NewArrivalCard({
  product,
  showNewFlag = true,
  onPress,
}: {
  product: SupplierProduct;
  showNewFlag?: boolean;
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
      accessibilityLabel={
        showNewFlag
          ? `New, ${product.name}, ${formatCents(product.priceCents)}`
          : `${product.name}, ${formatCents(product.priceCents)}`
      }
    >
      <View style={[styles.imageWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
        {photo ? (
          <Image source={{ uri: photo }} style={styles.image} resizeMode="contain" />
        ) : (
          <Package size={28} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />
        )}

        {showNewFlag && (
          <View style={[styles.flag, { backgroundColor: theme.colors.primary }]}>
            <Text style={[styles.flagText, { color: theme.colors.onPrimary }]}>NEW</Text>
          </View>
        )}

        {!product.inStock && (
          <View style={styles.outOfStock}>
            <Text style={styles.outOfStockText}>OUT OF STOCK</Text>
          </View>
        )}
      </View>

      <View style={styles.body}>
        <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={2}>
          {product.name}
        </Text>
        <Text style={[styles.price, { color: theme.colors.onSurface }]}>
          {formatCents(product.priceCents)}
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
  card: { width: NEW_ARRIVAL_CARD_WIDTH },
  // Taller than square -- see the docstring: the photo is the entire
  // argument for a product nobody has bought yet.
  imageWrap: {
    width: "100%",
    height: 168,
    borderRadius: radius.md,
    overflow: "hidden",
    alignItems: "center",
    justifyContent: "center",
  },
  image: { width: "100%", height: "100%" },
  flag: {
    position: "absolute",
    top: spacing.sm,
    left: spacing.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    borderRadius: radius.sm,
  },
  flagText: { ...typography.caption, fontWeight: "800", fontSize: 10, letterSpacing: 0.6 },
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
  body: { paddingTop: spacing.sm, gap: 1 },
  name: { ...typography.bodySmall, fontSize: 12, lineHeight: 16, fontWeight: "600" },
  price: { ...typography.body, fontWeight: "800" },
  unit: { ...typography.caption, fontSize: 11 },
});
