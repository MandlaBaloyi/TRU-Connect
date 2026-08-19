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
 * Product.isArchived docstring for why archiving, not deleting).
 */

import React from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Archive, ChevronRight, Pencil } from "lucide-react-native";

import { useArchiveProduct, useProduct } from "../hooks";
import { CATEGORY_OPTIONS, UNIT_OPTIONS } from "../types";
import { formatCents } from "../services/productMapper";
import { ImageCarousel } from "../components";
import { useInventoryItem } from "../../inventory/hooks";
import { InventoryStatusBadge } from "../../inventory/components";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

function labelFor<T extends string>(options: { value: T; label: string }[], value: T): string {
  return options.find((o) => o.value === value)?.label ?? value;
}

export default function ProductDetailScreen() {
  const { productId } = useLocalSearchParams<{ productId: string }>();
  const router = useRouter();
  const theme = useTheme();

  const { product, isLoading, isError, refetch } = useProduct(productId ?? "");
  const { archiveProduct, isArchiving } = useArchiveProduct();
  const { item: inventoryItem } = useInventoryItem(productId ?? "");

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
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Category</Text>
            <Text style={[styles.value, { color: theme.colors.onSurface }]}>
              {labelFor(CATEGORY_OPTIONS, product.category)}
            </Text>
          </View>

          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Price</Text>
            <Text style={[styles.value, { color: theme.colors.onSurface }]}>{formatCents(product.priceCents)}</Text>
          </View>

          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Sold as</Text>
            <Text style={[styles.value, { color: theme.colors.onSurface }]}>
              {labelFor(UNIT_OPTIONS, product.sellingUnit)}
            </Text>
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
  archiveRow: { marginTop: spacing.lg, alignItems: "center" },
  archiveButton: { flexDirection: "row", alignItems: "center", gap: spacing.xs, minHeight: 40, paddingHorizontal: spacing.md },
  archiveButtonText: { ...typography.body, fontWeight: "600" },
});
