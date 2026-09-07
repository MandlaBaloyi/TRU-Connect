import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Package, Users } from "lucide-react-native";

import { describeUnit, perUnitCents } from "@/components/products/unitEconomics";
import { calculateDiscount } from "../../../supplier/products/algorithms/discount";
import { formatCents } from "../../../supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { SupplierProductDetail } from "../../find-supplier/types";

/**
 * The top of a product page: what it is, what it costs, what you get,
 * and whether you can have it.
 *
 * WHAT THIS REPLACED. The page opened with a six-row label/value table
 * — Supplier, Product name, Price, Discount, Availability, Sold as —
 * which reads like a database dump, not a shop. Three specific
 * problems, all reported as "it doesn't convince you to buy":
 *
 *   1. It buried the price. The most important number on the page had
 *      the same weight as the product code.
 *   2. It repeated what was already on screen. Supplier and product
 *      name are both in the top bar; price is also in the buy bar.
 *   3. It answered questions nobody asked before the ones everybody
 *      asks. "Sold as: Pack" told a buyer nothing about what's IN the
 *      pack, which is the actual decision.
 *
 * WHAT AN INFORMAL BUYER IS ACTUALLY ASKING, in order, and where each
 * is answered here:
 *
 *   "What is it?"          -> the name, big, at the top
 *   "What does it cost?"   -> price, large, with the saving in rands
 *   "What do I get?"       -> "Pack of 6 bottles" + the per-item price
 *   "Can I get it now?"    -> a stock pill, not a table row
 *   "Will it sell?"        -> how many businesses already buy it
 *
 * PER-ITEM PRICE IS THE POINT OF THE WHOLE BLOCK. A pack of 6 and a
 * pack of 24 at the same price are completely different offers, and
 * comparing suppliers means comparing per-item cost. Doing that
 * arithmetic in your head, in a shop, from two phone screens, is the
 * friction this removes.
 */

/** Below this, "1 business bought this" reads as a warning rather than
 *  a recommendation -- the same reasoning as the supplier profile's own
 *  trust signals, which hide rather than show a lonely number. */
const MIN_BUYERS_TO_SHOW = 3;

export function ProductBuyBlock({ product }: { product: SupplierProductDetail }) {
  const theme = useTheme();
  const discount = calculateDiscount(product.priceCents, product.compareAtPriceCents);
  const unitText = describeUnit(product.sellingUnit, product.unitQuantity, product.unitMeasure);
  const perUnit = perUnitCents(product.priceCents, product.unitQuantity);

  return (
    <View style={styles.wrap}>
      <Text style={[styles.name, { color: theme.colors.onSurface }]}>{product.name}</Text>

      {/* THE PRICE IS NOT RED. It used to render in
          theme.colors.error -- the same token as "Out of stock" and
          every failure message in the app -- which meant a bargain
          wore the colour of a problem. Red sale prices are a real
          retail convention, but reusing the ERROR token for them
          conflates two opposite meanings in the theme, and dark text
          on white is the most readable option for the single most
          important number on the page. The discount badge and the
          saving keep the red: those are genuinely the "look here"
          parts. */}
      <View style={styles.priceRow}>
        <Text style={[styles.price, { color: theme.colors.onSurface }]}>
          {formatCents(product.priceCents)}
        </Text>
        {discount && product.compareAtPriceCents !== null && (
          <>
            <Text style={[styles.compareAt, { color: theme.colors.onSurfaceVariant }]}>
              {formatCents(product.compareAtPriceCents)}
            </Text>
            <View style={[styles.badge, { backgroundColor: theme.colors.errorContainer }]}>
              <Text style={[styles.badgeText, { color: theme.colors.error }]}>{discount.percentOff}% OFF</Text>
            </View>
          </>
        )}
      </View>

      {discount && product.compareAtPriceCents !== null && (
        <Text style={[styles.savings, { color: theme.colors.error }]}>
          Save {formatCents(product.compareAtPriceCents - product.priceCents)}
        </Text>
      )}

      {/* WHAT YOU GET FOR THAT PRICE. Renders only when there's real
          pack content -- an "Each" product has nothing to break down,
          and "Each · R200.00 each" would be noise. */}
      {(unitText || perUnit !== null) && (
        <View style={[styles.unitCard, { backgroundColor: theme.colors.surfaceVariant }]}>
          <Package size={16} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />
          <Text style={[styles.unitText, { color: theme.colors.onSurfaceVariant }]}>
            {unitText}
            {perUnit !== null && (
              <Text style={{ fontWeight: "700" }}>{`  ·  ${formatCents(perUnit)} each`}</Text>
            )}
          </Text>
        </View>
      )}

      <View style={styles.metaRow}>
        <View
          style={[
            styles.stockPill,
            { backgroundColor: product.inStock ? theme.colors.secondaryContainer : theme.colors.errorContainer },
          ]}
        >
          <Text
            style={[
              styles.stockText,
              { color: product.inStock ? theme.colors.secondary : theme.colors.error },
            ]}
          >
            {product.inStock ? "In stock" : "Out of stock"}
          </Text>
        </View>

        {product.buyerCount >= MIN_BUYERS_TO_SHOW && (
          <View style={styles.buyers}>
            <Users size={14} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />
            {/* "Bought by 3 businesses", not "3 businesses bought
                this". Two things were wrong with that phrasing: it
                ended on a dangling "this", and past tense matters --
                the data records COMPLETED orders, so "buy" claimed an
                ongoing habit the numbers don't support.
                Deliberately NOT "bought Cold drink Stocks": the
                product's name is three lines above this, in the
                largest text on the screen, so naming it again is
                repetition, not clarity. The count stays bold -- it's
                the part being scanned for. */}
            <Text style={[styles.buyersText, { color: theme.colors.onSurfaceVariant }]}>
              Bought by <Text style={styles.buyersCount}>{product.buyerCount}</Text>
              {product.buyerCount === 1 ? " business" : " businesses"}
            </Text>
          </View>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { paddingHorizontal: spacing.md, paddingTop: spacing.md, gap: spacing.xs },
  name: { ...typography.h1, fontWeight: "700", lineHeight: 28 },
  priceRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm, flexWrap: "wrap", marginTop: 2 },
  price: { fontSize: 26, fontWeight: "800" },
  compareAt: { ...typography.body, textDecorationLine: "line-through" },
  badge: { paddingHorizontal: spacing.sm, paddingVertical: 3, borderRadius: radius.pill },
  badgeText: { ...typography.bodySmall, fontWeight: "800", fontSize: 11 },
  savings: { ...typography.bodySmall, fontWeight: "700" },
  unitCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.md,
    marginTop: spacing.xs,
  },
  unitText: { ...typography.bodySmall, flex: 1 },
  metaRow: { flexDirection: "row", alignItems: "center", gap: spacing.md, marginTop: spacing.xs, flexWrap: "wrap" },
  stockPill: { paddingHorizontal: spacing.sm, paddingVertical: 4, borderRadius: radius.pill },
  stockText: { ...typography.bodySmall, fontWeight: "700", fontSize: 12 },
  buyers: { flexDirection: "row", alignItems: "center", gap: 5 },
  buyersText: { ...typography.bodySmall, fontSize: 12, fontWeight: "600" },
  buyersCount: { fontWeight: "800" },
});
