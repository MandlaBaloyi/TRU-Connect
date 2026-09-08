import React from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Package } from "lucide-react-native";

import { describeUnit, perUnitCents } from "@/components/products/unitEconomics";
import { formatCents } from "../../../../supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { SupplierProduct } from "../../types";

export const BULK_CARD_WIDTH = 172;

/**
 * A product in "Better per unit in bulk", led by its PER-UNIT price.
 *
 * THE ONE SECTION THAT OWES NOTHING TO CONSUMER APPS. Every other card
 * on this profile borrows a shape from retail; this one exists because
 * TRU Connect sells wholesale. A pack of 6 and a pack of 24 at the
 * same price are completely different offers, and an informal buyer
 * comparing two suppliers is really comparing per-item cost. Doing
 * that arithmetic in your head, in a shop, off two phone screens, is
 * the friction this removes -- see components/products/
 * unitEconomics.ts, which already had the maths and nothing had yet
 * put on a card.
 *
 * SO THE HIERARCHY IS INVERTED. The per-unit figure is the largest
 * text; the pack price is the smaller line beneath it. On every other
 * card that order is reversed, and that inversion IS the design: it
 * says at a glance that this strip is about value per item, not price
 * per purchase.
 *
 * A PRODUCT SOLD AS "EACH" RENDERS NO PER-UNIT LINE AT ALL, and falls
 * back to leading with the price. perUnitCents returns null rather
 * than the pack price for a quantity of one -- "R199.00 each" under an
 * R199.00 price implies a calculation happened when none did. The
 * server should not put such a product in this section; the card
 * handles it anyway rather than trusting that.
 *
 * NO ACTIONS ROW, unlike the category strips below. The heart /
 * comment / share icons stay on those cards, where the strip is a
 * catalogue and a business is browsing; here they were three taps
 * nobody takes eating the vertical space the PHOTO wants. A
 * merchandised card has one job -- make the product legible enough to
 * be chosen -- and the image is what does that job.
 */
export function BulkValueCard({
  product,
  onPress,
}: {
  product: SupplierProduct;
  onPress: () => void;
}) {
  const theme = useTheme();
  const photo = product.images[0] ?? null;
  const unit = describeUnit(product.sellingUnit, product.unitQuantity, product.unitMeasure);
  const perUnit = perUnitCents(product.priceCents, product.unitQuantity);

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        { borderColor: theme.colors.outlineVariant, backgroundColor: theme.colors.surface },
        pressed && { opacity: 0.85 },
      ]}
      accessibilityRole="button"
      accessibilityLabel={
        perUnit
          ? `${product.name}, ${formatCents(perUnit)} each, ${formatCents(product.priceCents)} for the pack`
          : `${product.name}, ${formatCents(product.priceCents)}`
      }
    >
      <View style={styles.row}>
        <View style={[styles.imageWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
          {photo ? (
            <Image source={{ uri: photo }} style={styles.image} resizeMode="contain" />
          ) : (
            <Package size={22} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />
          )}
        </View>

        <View style={styles.headline}>
          {perUnit !== null ? (
            <>
              <Text style={[styles.perUnit, { color: theme.colors.primary }]}>
                {formatCents(perUnit)}
              </Text>
              <Text style={[styles.perUnitLabel, { color: theme.colors.onSurfaceVariant }]}>each</Text>
            </>
          ) : (
            <Text style={[styles.perUnit, { color: theme.colors.onSurface }]}>
              {formatCents(product.priceCents)}
            </Text>
          )}
        </View>
      </View>

      <View style={styles.body}>
        <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={2}>
          {product.name}
        </Text>
        {perUnit !== null && (
          <Text style={[styles.packPrice, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
            {formatCents(product.priceCents)}
            {unit ? ` · ${unit}` : ""}
          </Text>
        )}
        {!product.inStock && (
          <Text style={[styles.outOfStock, { color: theme.colors.error }]}>Out of stock</Text>
        )}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { width: BULK_CARD_WIDTH, borderWidth: 1, borderRadius: radius.md, overflow: "hidden" },
  row: { flexDirection: "row", alignItems: "center" },
  imageWrap: { width: 72, height: 72, alignItems: "center", justifyContent: "center" },
  image: { width: "100%", height: "100%" },
  headline: { flex: 1, alignItems: "center", justifyContent: "center", paddingRight: spacing.sm },
  perUnit: { ...typography.h2, fontWeight: "800" },
  perUnitLabel: { ...typography.caption, fontSize: 11, marginTop: -2 },
  body: { paddingHorizontal: spacing.sm, paddingBottom: spacing.sm, gap: 2 },
  name: { ...typography.bodySmall, fontSize: 12, lineHeight: 16, fontWeight: "600" },
  packPrice: { ...typography.caption, fontSize: 11 },
  outOfStock: { ...typography.caption, fontSize: 11, fontWeight: "700" },
});
