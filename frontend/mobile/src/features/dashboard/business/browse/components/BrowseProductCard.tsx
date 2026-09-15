import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Users } from "lucide-react-native";

import { CategoryImage } from "@/components/categories";
// Same formatter the supplier catalogue card uses. It lives in a
// feature folder rather than utils/, which is its own small smell,
// but a second copy would be a worse one.
import { SupplierName } from "@/components/ui/SupplierName";
import { formatCents } from "@/features/dashboard/supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { BrowseProduct } from "../types";

/**
 * One product, in a browse that MIXES SUPPLIERS.
 *
 * THE SUPPLIER LINE IS NOT DECORATION. On a shopfront every card is
 * from the same shop and naming it would be noise; here the next card
 * down is somebody else's, and a shopkeeper who taps without reading
 * ends up in the wrong shop. So the supplier is on every card, always.
 *
 * "ALSO FROM N SUPPLIERS" IS THE RESOLVED CATALOGUE MADE VISIBLE. It is
 * zero today because nothing is matched yet, and the card simply does
 * not mention it -- an honest empty state rather than "also from 0".
 * The day matching links these offers the line appears by itself.
 *
 * A COUNT, NEVER A COMPARISON. V2_04 2.4: comparison is framed as a
 * saving for the buyer, never as suppliers ranked against each other.
 * This says how many others carry it, not who is cheaper.
 */
export function BrowseProductCard({
  product,
  onPress,
}: {
  product: BrowseProduct;
  onPress?: () => void;
}) {
  const theme = useTheme();
  const discounted =
    product.compareAtPriceCents !== null && product.compareAtPriceCents > product.priceCents;

  return (
    <Pressable
      onPress={onPress}
      android_ripple={{ color: theme.colors.surfaceVariant }}
      style={({ pressed }) => [
        styles.card,
        {
          backgroundColor: pressed ? theme.colors.surfaceVariant : theme.colors.surface,
          borderColor: theme.colors.outlineVariant,
        },
      ]}
      accessibilityRole="button"
      accessibilityLabel={`${product.name}, ${formatCents(product.priceCents)}, from ${product.supplierName}`}
    >
      <View style={styles.imageWrap}>
        <CategoryImage
          photoUrl={product.imageUrl}
          category={product.category}
          fill
          resizeMode="contain"
        />
      </View>

      <View style={styles.body}>
        <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={2}>
          {product.name}
        </Text>

        <View style={styles.priceRow}>
          <Text style={[styles.price, { color: theme.colors.onSurface }]}>
            {formatCents(product.priceCents)}
          </Text>
          {discounted && (
            <Text style={[styles.was, { color: theme.colors.onSurfaceVariant }]}>
              {formatCents(product.compareAtPriceCents as number)}
            </Text>
          )}
        </View>

        <SupplierName
          name={product.supplierName}
          verificationStatus={product.supplierVerificationStatus}
          style={[styles.supplier, { color: theme.colors.onSurfaceVariant }]}
          tickSize={12}
        />

        {product.buyerLabel ? (
          // ABOVE "also from N suppliers" on purpose. That line is
          // about OUR catalogue; this one is about what other shops
          // actually did, and it is the more persuasive of the two.
          // The sentence itself comes from the server so this screen
          // and the Community feed cannot word it differently.
          <View style={styles.buyersRow}>
            <Users size={12} color={theme.colors.primary} strokeWidth={2.4} />
            <Text style={[styles.buyers, { color: theme.colors.primary }]} numberOfLines={1}>
              {product.buyerLabel}
            </Text>
          </View>
        ) : null}

        {product.alternativeCount > 0 && (
          <Text style={[styles.alternatives, { color: theme.colors.primary }]} numberOfLines={1}>
            Also from {product.alternativeCount}{" "}
            {product.alternativeCount === 1 ? "supplier" : "suppliers"}
          </Text>
        )}

        {!product.inStock && (
          <Text style={[styles.outOfStock, { color: theme.colors.onSurfaceVariant }]}>
            Out of stock
          </Text>
        )}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { flex: 1, borderRadius: radius.md, borderWidth: 1, overflow: "hidden" },
  imageWrap: { width: "100%", aspectRatio: 1 },
  body: { padding: spacing.sm, gap: 2 },
  name: { ...typography.body, fontWeight: "600" },
  priceRow: { flexDirection: "row", alignItems: "baseline", gap: spacing.xs },
  price: { ...typography.body, fontWeight: "700" },
  was: { ...typography.caption, textDecorationLine: "line-through" },
  supplier: { ...typography.caption },
  buyers: { ...typography.caption, fontWeight: "700", flexShrink: 1 },
  buyersRow: { flexDirection: "row", alignItems: "center", gap: 3 },
  alternatives: { ...typography.caption, fontWeight: "600" },
  outOfStock: { ...typography.caption, fontStyle: "italic" },
});
