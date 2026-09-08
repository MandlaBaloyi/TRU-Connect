import React from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Package, Plus } from "lucide-react-native";

import { calculateDiscount } from "../../../../supplier/products/algorithms/discount";
import { describeUnit, perUnitCents } from "@/components/products/unitEconomics";
import { formatCents } from "../../../../supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { SupplierProduct } from "../../types";

/**
 * ONE product, full width -- the supplier's own pick, at the top of
 * their storefront.
 *
 * THE ONLY FULL-WIDTH PRODUCT ON THE SCREEN, and that is its entire
 * job. Everything else on this profile is a card in a sideways strip;
 * this breaks that rhythm on purpose, because a strip cannot say "look
 * at this one first" -- every card in a strip is visually equal to the
 * one beside it, which is what makes strips good at browsing and
 * useless at pointing.
 *
 * ONE PER PROFILE, enforced by the contract (FEATURED_PRODUCT is a
 * single product, not a list). Two of these would be two things
 * shouting, which is the same as none.
 *
 * HORIZONTAL, NOT A BIG SQUARE HERO. A full-bleed image would push the
 * actual products below the fold on a phone -- the exact complaint
 * that shrank the trust card earlier in this build. Image left, the
 * decision on the right, one row.
 *
 * SHOWS BOTH PRICES WHEN THERE IS SOMETHING TO SAY: the saving if it
 * is discounted, the per-unit price if it comes in a pack. This is the
 * one card with room for both, so it is the one card that should.
 */
export function FeaturedProductBanner({
  label,
  product,
  onPress,
  onAddToCart,
  isAdding = false,
}: {
  label: string;
  product: SupplierProduct;
  onPress: () => void;
  onAddToCart?: () => void;
  isAdding?: boolean;
}) {
  const theme = useTheme();
  const photo = product.images[0] ?? null;
  const discount = calculateDiscount(product.priceCents, product.compareAtPriceCents);
  const unit = describeUnit(product.sellingUnit, product.unitQuantity, product.unitMeasure);
  const perUnit = perUnitCents(product.priceCents, product.unitQuantity);

  return (
    <View style={styles.wrap}>
      <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>{label}</Text>

      <Pressable
        onPress={onPress}
        style={({ pressed }) => [
          styles.card,
          { borderColor: theme.colors.outlineVariant, backgroundColor: theme.colors.surface },
          pressed && { opacity: 0.9 },
        ]}
        accessibilityRole="button"
        accessibilityLabel={`${label}: ${product.name}, ${formatCents(product.priceCents)}`}
      >
        <View style={[styles.imageWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
          {photo ? (
            <Image source={{ uri: photo }} style={styles.image} resizeMode="contain" />
          ) : (
            <Package size={30} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />
          )}
        </View>

        <View style={styles.body}>
          <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={2}>
            {product.name}
          </Text>

          <View style={styles.priceRow}>
            <Text style={[styles.price, { color: theme.colors.onSurface }]}>
              {formatCents(product.priceCents)}
            </Text>
            {discount && product.compareAtPriceCents !== null && (
              <Text style={[styles.was, { color: theme.colors.onSurfaceVariant }]}>
                {formatCents(product.compareAtPriceCents)}
              </Text>
            )}
          </View>

          {/* The rand amount, not the percentage -- direct feedback:
              "rather than saying you save R50, says save R50". */}
          {discount && product.compareAtPriceCents !== null && (
            <Text style={[styles.saving, { color: theme.colors.error }]}>
              Save {formatCents(product.compareAtPriceCents - product.priceCents)}
            </Text>
          )}

          {(unit || perUnit !== null) && (
            <Text style={[styles.unit, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
              {[unit, perUnit !== null ? `${formatCents(perUnit)} each` : null].filter(Boolean).join(" · ")}
            </Text>
          )}

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
              accessibilityLabel={
                product.inStock ? `Add ${product.name} to cart` : `${product.name} is out of stock`
              }
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
                {isAdding ? "Adding…" : product.inStock ? "Add to cart" : "Out of stock"}
              </Text>
            </Pressable>
          )}
        </View>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { paddingHorizontal: spacing.md, gap: spacing.xs },
  label: {
    ...typography.caption,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 0.6,
  },
  // alignItems CENTER, not the default stretch: the image column is a
  // fixed square, and stretching it to whatever height the body
  // happens to be is what produced the bug below.
  card: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: radius.lg,
    overflow: "hidden",
  },
  // A DEFINITE HEIGHT, and it has to be. This had a width and no
  // height, so the Image's own height: "100%" had no parent height to
  // resolve against -- Yoga fell back to the photo's INTRINSIC height
  // (these are ~600px tall), the column grew to match, and because a
  // row stretches its children by default the entire card grew with
  // it. On a real phone the banner filled the whole screen with one
  // product. Any fixed-size image box in this app needs both
  // dimensions, never one plus a percentage.
  imageWrap: { width: 118, height: 118, alignItems: "center", justifyContent: "center" },
  image: { width: "100%", height: "100%" },
  body: { flex: 1, padding: spacing.md, gap: 2 },
  name: { ...typography.body, fontWeight: "700" },
  priceRow: { flexDirection: "row", alignItems: "baseline", gap: 8, flexWrap: "wrap" },
  price: { ...typography.h2, fontWeight: "800" },
  was: { ...typography.bodySmall, textDecorationLine: "line-through" },
  saving: { ...typography.bodySmall, fontSize: 12, fontWeight: "800" },
  unit: { ...typography.caption, fontSize: 11 },
  addButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    minHeight: 38,
    borderRadius: radius.md,
    marginTop: spacing.sm,
  },
  addLabel: { ...typography.bodySmall, fontWeight: "700" },
});
