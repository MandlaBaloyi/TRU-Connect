import React from "react";
import { ActivityIndicator, FlatList, Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { ChevronRight, Package, Plus } from "lucide-react-native";

import { ProductActionsRow } from "@/components/products/ProductActionsRow";
import { calculateDiscount } from "../../../supplier/products/algorithms/discount";
import { sellingUnitLabel } from "@/components/products/sellingUnitLabel";
import { formatCents } from "../../../supplier/products/services/productMapper";
import { CATEGORY_OPTIONS } from "../../../supplier/products/types";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { SupplierProduct, SupplierShowcaseCategory } from "../types";

/**
 * The supplier's storefront on their brand profile: a vertical stack
 * of category sections (their real product categories, biggest first,
 * <=5 -- resolved server-side), each a horizontal strip of up to 6
 * products with a "See all in <category>" into the full catalogue,
 * pre-filtered. The supplier's pinned picks already arrive first
 * within each strip from the backend (no badge -- a business just sees
 * a well-ordered strip).
 *
 * Products with no image are never in `categories` (the backend
 * excludes them) -- a blank card would undermine the storefront.
 */
interface Props {
  categories: SupplierShowcaseCategory[];
  isLoading: boolean;
  onSeeAll: (category: string) => void;
  /** name rides along so the product screen's own top bar is right
   *  on its first frame -- see business/routes.ts. */
  onProductPress: (productId: string, productName: string) => void;
  /** Add straight from the brand profile -- the same reasoning as the
   *  catalogue grid: a repeat buyer shouldn't have to open a product
   *  page to add something they already know they want. */
  onAddToCart?: (product: SupplierProduct) => void;
  addingProductId?: string | null;
}

const CARD_WIDTH = 148;

function labelFor(category: string): string {
  return CATEGORY_OPTIONS.find((o) => o.value === category)?.label ?? category;
}

export function SupplierShowcase({
  categories,
  isLoading,
  onSeeAll,
  onProductPress,
  onAddToCart,
  addingProductId,
}: Props) {
  const theme = useTheme();

  if (isLoading) {
    return (
      <View style={styles.centre}>
        <ActivityIndicator color={theme.colors.primary} />
      </View>
    );
  }

  if (categories.length === 0) {
    return (
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>Products</Text>
        <Text style={[styles.empty, { color: theme.colors.onSurfaceVariant }]}>
          This supplier hasn't added products with photos yet.
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.wrap}>
      {categories.map((group) => (
        <View key={group.category} style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>{labelFor(group.category)}</Text>
            <Pressable
              onPress={() => onSeeAll(group.category)}
              hitSlop={8}
              style={styles.seeAll}
              accessibilityRole="button"
              accessibilityLabel={`See all in ${labelFor(group.category)}`}
            >
              <Text style={[styles.seeAllText, { color: theme.colors.primary }]}>See all</Text>
              <ChevronRight size={15} color={theme.colors.primary} strokeWidth={2.4} />
            </Pressable>
          </View>

          <FlatList
            horizontal
            data={group.products}
            keyExtractor={(item) => item.id}
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.list}
            renderItem={({ item }) => (
              <ShowcaseCard
                product={item}
                onPress={() => onProductPress(item.id, item.name)}
                onAddToCart={onAddToCart ? () => onAddToCart(item) : undefined}
                isAdding={addingProductId === item.id}
              />
            )}
          />
        </View>
      ))}
    </View>
  );
}

function ShowcaseCard({
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
  const unitLabel = sellingUnitLabel(product.sellingUnit, product.unitQuantity, product.unitMeasure);

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        { borderColor: theme.colors.outlineVariant, backgroundColor: theme.colors.surface },
        pressed && { opacity: 0.85 },
      ]}
      accessibilityRole="button"
      accessibilityLabel={`View ${product.name}`}
    >
      <View style={[styles.imageWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
        {photo ? (
          <Image source={{ uri: photo }} style={styles.image} resizeMode="contain" />
        ) : (
          <Package size={26} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />
        )}
        {discount && (
          <View style={[styles.discountBadge, { backgroundColor: theme.colors.error }]}>
            <Text style={styles.discountBadgeText}>{discount.percentOff}% OFF</Text>
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
        <View style={styles.priceRow}>
          <Text style={[styles.price, { color: theme.colors.onSurface }]}>
            {formatCents(product.priceCents)}
          </Text>
          {discount && product.compareAtPriceCents !== null && (
            <Text style={[styles.compareAt, { color: theme.colors.onSurfaceVariant }]}>
              {formatCents(product.compareAtPriceCents)}
            </Text>
          )}
        </View>
        {/* The unit the price is quoted in -- see sellingUnitLabel on
            why a bare price is unusable for a wholesale decision. */}
        {unitLabel && (
          <Text style={[styles.unitLabel, { color: theme.colors.onSurfaceVariant }]}>{unitLabel}</Text>
        )}
        {/* The same three actions the catalogue grid has -- these two
            cards had drifted, so the same product looked like a
            different kind of object depending on which screen you
            found it on. One shared component now. */}
        {onAddToCart && (
          <Pressable
            onPress={(event) => {
              // The card itself navigates; adding must not.
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
              size={14}
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

        <ProductActionsRow productName={product.name} size={18} />
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
    minHeight: 32,
    borderRadius: radius.md,
    marginTop: spacing.xs,
  },
  addLabel: { ...typography.bodySmall, fontWeight: "700", fontSize: 12 },
  unitLabel: { ...typography.bodySmall, fontSize: 11, marginTop: 1 },
  wrap: { gap: spacing.lg },
  centre: { height: 140, alignItems: "center", justifyContent: "center" },
  section: { gap: spacing.sm },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.md,
  },
  sectionTitle: { ...typography.h2, fontWeight: "700" },
  seeAll: { flexDirection: "row", alignItems: "center", gap: 2 },
  seeAllText: { ...typography.bodySmall, fontWeight: "700" },
  empty: { ...typography.bodySmall, paddingHorizontal: spacing.md },
  list: { paddingHorizontal: spacing.md, gap: spacing.sm },
  card: { width: CARD_WIDTH, borderWidth: 1, borderRadius: radius.md, overflow: "hidden" },
  imageWrap: { width: "100%", aspectRatio: 1, alignItems: "center", justifyContent: "center" },
  image: { width: "100%", height: "100%" },
  discountBadge: { position: "absolute", top: spacing.xs, left: spacing.xs, paddingHorizontal: 7, paddingVertical: 2, borderRadius: 3 },
  discountBadgeText: { color: "#FFFFFF", fontSize: 9, fontWeight: "700" },
  outOfStock: {
    position: "absolute",
    bottom: spacing.xs,
    left: spacing.xs,
    right: spacing.xs,
    backgroundColor: "rgba(0,0,0,0.75)",
    borderRadius: 3,
    paddingVertical: 2,
    alignItems: "center",
  },
  outOfStockText: { color: "#FFFFFF", fontSize: 9, fontWeight: "700", letterSpacing: 0.4 },
  body: { padding: spacing.sm, gap: 2 },
  name: { ...typography.bodySmall, fontWeight: "700" },
  priceRow: { flexDirection: "row", alignItems: "center", flexWrap: "wrap", gap: 5 },
  price: { ...typography.bodySmall, fontWeight: "700" },
  compareAt: { ...typography.caption, textDecorationLine: "line-through" },
});
