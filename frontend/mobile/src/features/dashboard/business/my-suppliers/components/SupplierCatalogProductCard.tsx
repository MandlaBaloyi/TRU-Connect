import React from "react";
import { Alert, Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Heart, MessagesSquare, Package, Share2 } from "lucide-react-native";

import { calculateDiscount } from "../../../supplier/products/algorithms/discount";
import { formatCents } from "../../../supplier/products/services/productMapper";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { SupplierProduct } from "../../find-supplier/types";

interface Props {
  product: SupplierProduct;
  onPress: () => void;
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
export function SupplierCatalogProductCard({ product, onPress, cardStyle }: Props) {
  const theme = useTheme();
  const discount = calculateDiscount(product.priceCents, product.compareAtPriceCents);
  const photoUrl = product.images[0] ?? null;

  const comingSoon = (feature: string) => {
    Alert.alert("Coming soon", `${feature} isn't available yet, but it's on the way.`);
  };

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
        {photoUrl ? (
          <Image source={{ uri: photoUrl }} style={styles.image} resizeMode="contain" />
        ) : (
          <View style={styles.fallback}>
            <Package size={28} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />
          </View>
        )}
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
          <Text style={[styles.price, { color: discount ? theme.colors.error : theme.colors.onSurface }]}>
            {formatCents(product.priceCents)}
          </Text>
          {discount && product.compareAtPriceCents !== null && (
            <Text style={[styles.compareAtPrice, { color: theme.colors.onSurfaceVariant }]}>
              {formatCents(product.compareAtPriceCents)}
            </Text>
          )}
        </View>

        <View style={styles.actionsRow}>
          <Pressable
            onPress={() => comingSoon("Likes")}
            hitSlop={8}
            style={styles.actionButton}
            accessibilityRole="button"
            accessibilityLabel={`Like ${product.name}`}
          >
            <Heart size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2.5} />
          </Pressable>
          <Pressable
            onPress={() => comingSoon("Comments")}
            hitSlop={8}
            style={styles.actionButton}
            accessibilityRole="button"
            accessibilityLabel={`Comment on ${product.name}`}
          >
            <MessagesSquare size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2.5} />
          </Pressable>
          <Pressable
            onPress={() => comingSoon("Sharing")}
            hitSlop={8}
            style={styles.actionButton}
            accessibilityRole="button"
            accessibilityLabel={`Share ${product.name}`}
          >
            <Share2 size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2.5} />
          </Pressable>
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
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
  image: { width: "100%", height: "100%" },
  fallback: { alignItems: "center", justifyContent: "center" },
  discountBadge: { position: "absolute", top: spacing.xs, left: spacing.xs, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 3 },
  discountBadgeText: { color: "#FFFFFF", fontSize: 10, fontWeight: "700" },
  outOfStockOverlay: {
    ...StyleSheet.absoluteFillObject,
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
  actionsRow: { flexDirection: "row", gap: spacing.md, marginTop: spacing.xs },
  actionButton: { padding: 2 },
});
