/**
 * ProductDetailScreen — reached by tapping a product on the list.
 * Image carousel, then the fields the list itself keeps narrow
 * (category, unit), then two actions.
 *
 * STOCK NOW COMES FROM INVENTORY, NOT product.stockStatus -- same
 * migration as ProductCard's own (see that component's docstring for
 * the full reasoning). This screen fetches its own inventory record
 * via useInventoryItem alongside the product itself; "View in
 * Inventory" links to the real Inventory detail screen for anything
 * beyond just checking the status (quantity, threshold, adjusting
 * stock all live there now, not here).
 *
 * EDIT NOW NAVIGATES TO A REAL SCREEN (EditProductScreen) -- was shown
 * disabled/"coming soon" until that screen existed; see this feature's
 * own products/[productId]/edit.tsx route and EditProductScreen.tsx.
 *
 * ARCHIVE IS REAL AND DELIBERATELY SEPARATED -- per review ("archive
 * should sit a little further from the [other buttons], with its own
 * icon"): visually distanced below Edit, its own Archive icon instead
 * of matching Edit's button style, and a confirmation dialog before it
 * fires, since it's a real state change (see types.ts's own
 * Product.isArchived docstring for why archiving, not deleting, is the
 * DEFAULT action -- true deletion is a separate, further action below).
 *
 * ARCHIVED PRODUCTS GET Unarchive + Delete IN THE SAME SPOT --
 * previously this showed only a static "Archived" label with no way
 * back from the individual screen at all (only Bulk Edit's own
 * Archived tab could unarchive/delete). Delete is a real, permanent
 * removal from the supplier's own point of view (soft-deleted on the
 * backend, kept intact for future analysis, never actually visible
 * again) -- gets its own confirmation dialog, same discipline as
 * Archive's.
 */

import React, { useState } from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Archive, ArchiveRestore, ChevronRight, Pencil, Trash2 } from "lucide-react-native";

import { useArchiveProduct, useDeleteProduct, useProduct, useUnarchiveProduct } from "../hooks";
import { CATEGORY_OPTIONS, UNIT_OPTIONS } from "../types";
import { calculateDiscount } from "../algorithms/discount";
import { formatCents } from "../services/productMapper";
import { ImageCarousel } from "../components";
import { useInventoryItem } from "../../inventory/hooks";
import { InventoryStatusBadge } from "../../inventory/components";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/** How many lines a long description shows before "Read more" --
 *  matches the real, worth-truncating case found during review
 *  (a description running several paragraphs, shown in full with no
 *  truncation at all). */
const DESCRIPTION_COLLAPSED_LINES = 4;

function labelFor<T extends string>(options: { value: T; label: string }[], value: T): string {
  return options.find((o) => o.value === value)?.label ?? value;
}

export default function ProductDetailScreen() {
  const { productId } = useLocalSearchParams<{ productId: string }>();
  const router = useRouter();
  const theme = useTheme();

  const { product, isLoading, isError, refetch } = useProduct(productId ?? "");
  const { archiveProduct, isArchiving } = useArchiveProduct();
  const { unarchiveProduct, isUnarchiving } = useUnarchiveProduct();
  const { deleteProduct, isDeleting } = useDeleteProduct();
  const { item: inventoryItem } = useInventoryItem(productId ?? "");
  const [descriptionExpanded, setDescriptionExpanded] = useState(false);
  // Only actually true once RN reports the real text overflowed the
  // collapsed line count -- "Read more" must never appear for a SHORT
  // description that would happily fit in 4 lines on its own.
  const [descriptionTruncated, setDescriptionTruncated] = useState(false);

  const handleArchive = () => {
    if (!product) return;
    Alert.alert(
      "Archive this product?",
      "It will no longer be visible to businesses. Past orders that reference it are unaffected.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Archive",
          style: "destructive",
          onPress: async () => {
            await archiveProduct(product.id);
            router.back();
          },
        },
      ]
    );
  };

  const handleUnarchive = async () => {
    if (!product) return;
    await unarchiveProduct(product.id);
  };

  const handleDelete = () => {
    if (!product) return;
    Alert.alert(
      "Delete this product?",
      "This removes it from your shop everywhere. This can't be undone from the app.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            await deleteProduct(product.id);
            router.back();
          },
        },
      ]
    );
  };

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !product) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load this product. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader paddingHorizontal={0}>
      <ScrollView contentContainerStyle={styles.content}>
        <ImageCarousel images={product.images} />

        <View style={styles.body}>
          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Product name</Text>
            <Text style={[styles.value, { color: theme.colors.onSurface }]}>{product.name}</Text>
          </View>

          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Product code</Text>
            <Text style={[styles.value, { color: theme.colors.onSurface }]}>{product.productCode}</Text>
            <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>
              Shown to businesses when they order -- never editable.
            </Text>
          </View>

          {product.description && (
            <View style={styles.field}>
              <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Description</Text>

              {/* THE ACTUAL FIX -- a separate, invisible copy of the
                  same text with NO numberOfLines limit, purely to
                  measure how many lines it would genuinely need.
                  height:0 + overflow:hidden keeps it in normal layout
                  flow (so its WIDTH correctly matches the visible
                  text's own wrapping) while taking up zero visual
                  space. This has to be a SEPARATE element -- once
                  numberOfLines is applied to the VISIBLE text below,
                  its own onTextLayout only ever reports the already-
                  truncated line count (max 4), never the true total,
                  so "lines.length > 4" could never fire on that one. */}
              <View style={styles.measurer} pointerEvents="none">
                <Text
                  style={[styles.value, styles.descriptionText, { color: theme.colors.onSurface }]}
                  onTextLayout={(event) => {
                    if (event.nativeEvent.lines.length > DESCRIPTION_COLLAPSED_LINES) {
                      setDescriptionTruncated(true);
                    }
                  }}
                >
                  {product.description}
                </Text>
              </View>

              <Text
                style={[styles.value, styles.descriptionText, { color: theme.colors.onSurface }]}
                numberOfLines={descriptionExpanded ? undefined : DESCRIPTION_COLLAPSED_LINES}
              >
                {product.description}
              </Text>
              {descriptionTruncated && (
                <Pressable
                  onPress={() => setDescriptionExpanded((prev) => !prev)}
                  accessibilityRole="button"
                  accessibilityLabel={descriptionExpanded ? "Show less" : "Read more"}
                >
                  <Text style={[styles.readMore, { color: theme.colors.primary }]}>
                    {descriptionExpanded ? "Show less" : "Read more"}
                  </Text>
                </Pressable>
              )}
            </View>
          )}

          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Category</Text>
            <Text style={[styles.value, { color: theme.colors.onSurface }]}>
              {labelFor(CATEGORY_OPTIONS, product.category)}
            </Text>
          </View>

          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Price</Text>
            <View style={styles.priceRow}>
              <Text style={[styles.value, { color: theme.colors.onSurface }]}>{formatCents(product.priceCents)}</Text>
              {product.compareAtPriceCents !== null && (
                <Text style={[styles.compareAtPrice, { color: theme.colors.onSurfaceVariant }]}>
                  {formatCents(product.compareAtPriceCents)}
                </Text>
              )}
              {(() => {
                const discount = calculateDiscount(product.priceCents, product.compareAtPriceCents);
                return (
                  discount && (
                    <View style={[styles.discountBadge, { backgroundColor: theme.colors.errorContainer }]}>
                      <Text style={[styles.discountBadgeText, { color: theme.colors.error }]}>
                        {discount.percentOff}% OFF
                      </Text>
                    </View>
                  )
                );
              })()}
            </View>
          </View>

          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Sold as</Text>
            <Text style={[styles.value, { color: theme.colors.onSurface }]}>
              {labelFor(UNIT_OPTIONS, product.sellingUnit)}
            </Text>
          </View>

          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>SKU</Text>
            <Text style={[styles.value, { color: theme.colors.onSurface }]}>{product.sku}</Text>
          </View>

          {!product.isArchived && (
            <Pressable
              onPress={() => router.push(`/supplier/inventory/${product.id}`)}
              style={styles.field}
              accessibilityRole="button"
              accessibilityLabel="View in Inventory"
            >
              <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Stock</Text>
              <View style={styles.stockRow}>
                {inventoryItem ? (
                  <>
                    <InventoryStatusBadge status={inventoryItem.status} />
                    <Text style={[styles.stockAvailable, { color: theme.colors.onSurfaceVariant }]}>
                      • {inventoryItem.availableQuantity} available
                    </Text>
                  </>
                ) : (
                  <ActivityIndicator size="small" color={theme.colors.onSurfaceVariant} />
                )}
                <View style={styles.stockRowSpacer} />
                <Text style={[styles.viewInventoryLink, { color: theme.colors.primary }]}>View in Inventory</Text>
                <ChevronRight size={16} color={theme.colors.primary} />
              </View>
            </Pressable>
          )}

          {product.isArchived && (
            <View style={styles.field}>
              <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Stock</Text>
              <Text style={[styles.value, { color: theme.colors.onSurfaceVariant }]}>Archived</Text>
            </View>
          )}

          <Pressable
            onPress={() => router.push(`/supplier/products/${product.id}/edit`)}
            style={[styles.editButton, { borderColor: theme.colors.primary, backgroundColor: theme.colors.surface }]}
            accessibilityRole="button"
            accessibilityLabel="Edit product"
          >
            <Pencil size={18} color={theme.colors.primary} strokeWidth={2} />
            <Text style={[styles.editButtonText, { color: theme.colors.primary }]}>Edit Product</Text>
          </Pressable>

          {!product.isArchived && (
            <View style={styles.archiveRow}>
              <Pressable
                onPress={isArchiving ? undefined : handleArchive}
                disabled={isArchiving}
                style={styles.archiveButton}
                accessibilityRole="button"
                accessibilityLabel="Archive product"
              >
                <Archive size={16} color={theme.colors.error} strokeWidth={2} />
                <Text style={[styles.archiveButtonText, { color: theme.colors.error }]}>
                  {isArchiving ? "Archiving..." : "Archive Product"}
                </Text>
              </Pressable>
            </View>
          )}

          {product.isArchived && (
            <View style={styles.archiveRow}>
              <Pressable
                onPress={isUnarchiving ? undefined : handleUnarchive}
                disabled={isUnarchiving}
                style={styles.archiveButton}
                accessibilityRole="button"
                accessibilityLabel="Unarchive product"
              >
                <ArchiveRestore size={16} color={theme.colors.onSurface} strokeWidth={2} />
                <Text style={[styles.archiveButtonText, { color: theme.colors.onSurface }]}>
                  {isUnarchiving ? "Unarchiving..." : "Unarchive Product"}
                </Text>
              </Pressable>
              <Pressable
                onPress={isDeleting ? undefined : handleDelete}
                disabled={isDeleting}
                style={styles.archiveButton}
                accessibilityRole="button"
                accessibilityLabel="Delete product"
              >
                <Trash2 size={16} color={theme.colors.error} strokeWidth={2} />
                <Text style={[styles.archiveButtonText, { color: theme.colors.error }]}>
                  {isDeleting ? "Deleting..." : "Delete Product"}
                </Text>
              </Pressable>
            </View>
          )}
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  content: { paddingBottom: spacing.xxl },
  body: { padding: spacing.md, gap: spacing.lg },
  field: { gap: spacing.xs },
  label: { ...typography.bodySmall },
  value: { ...typography.body, fontWeight: "600" },
  descriptionText: { fontWeight: "400" },
  measurer: { height: 0, overflow: "hidden" },
  readMore: { ...typography.bodySmall, fontWeight: "700", marginTop: 4 },
  hint: { ...typography.caption },
  priceRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  compareAtPrice: { ...typography.bodySmall, textDecorationLine: "line-through" },
  discountBadge: { paddingHorizontal: spacing.xs, paddingVertical: 2, borderRadius: radius.sm },
  discountBadgeText: { ...typography.caption, fontWeight: "700" },
  stockRow: { flexDirection: "row", alignItems: "center", gap: 4 },
  stockAvailable: { ...typography.bodySmall },
  stockRowSpacer: { flex: 1 },
  viewInventoryLink: { ...typography.bodySmall, fontWeight: "600" },
  editButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
    minHeight: 52,
    borderWidth: 1,
    borderRadius: radius.md,
    marginTop: spacing.md,
  },
  editButtonText: { ...typography.body, fontWeight: "600" },
  archiveRow: { marginTop: spacing.lg, alignItems: "center", gap: spacing.sm },
  archiveButton: { flexDirection: "row", alignItems: "center", gap: spacing.xs, minHeight: 40, paddingHorizontal: spacing.md },
  archiveButtonText: { ...typography.body, fontWeight: "600" },
});
