/**
 * ProductsScreen — "what do I sell." Compact vertical list, never a
 * grid. Search is local/instant once the list is loaded, never a
 * network request per keystroke.
 *
 * DELIBERATELY SIMPLE, ONE-PRODUCT-AT-A-TIME -- per review, this
 * screen is for a supplier managing roughly 1-50 products individually
 * (view, add, edit, archive one at a time), the same role Loan Book/
 * Order Book each play for their own single-item workflows. Bulk
 * operations (100+ products, mass actions) are a genuinely different
 * workflow with a different screen, see
 * ../../bulk-products/screens/BulkEditScreen.tsx.
 *
 * Two compact shortcuts (Bulk Upload, Bulk Edit) on the count row, and
 * the header "⋮" menu (Export/Sort/Download Template/Download Guide),
 * are PURE NAVIGATION AND UTILITY ACTIONS -- no bulk-edit logic,
 * state, or components live in this file. Export and Sort are real,
 * local-to-this-screen concerns (a Products action, not a Bulk
 * Products one), which is why they're built here rather than in
 * bulk-products/; Download Template/Guide reuse bulk-products' own
 * services/downloadDocuments.ts rather than duplicating those files.
 */

import React, { useLayoutEffect, useMemo, useState } from "react";
import { ActivityIndicator, Alert, FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from "react-native";
import { useNavigation, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { ListChecks, Plus, UploadCloud } from "lucide-react-native";

import { useProducts } from "../hooks";
import type { Product, ProductListFilter, SortOption } from "../types";
import {
  EmptyProducts,
  ProductCard,
  ProductSearchBar,
  ProductsOverflowMenu,
  ProductStatusFilterBar,
  SortOptionsSheet,
} from "../components";
import { sortProducts } from "../algorithms/sortProducts";
import { exportProducts } from "../services/exportProducts";
import { downloadImportGuide, downloadImportTemplate } from "../../bulk-products/services/downloadDocuments";
import { useInventoryList } from "../../inventory/hooks";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

export default function ProductsScreen() {
  const router = useRouter();
  const navigation = useNavigation();
  const theme = useTheme();

  const [searchTerm, setSearchTerm] = useState("");
  const [listFilter, setListFilter] = useState<ProductListFilter>("ALL");
  const [sortOption, setSortOption] = useState<SortOption>("NEWEST");
  const [sortSheetOpen, setSortSheetOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  // IN_STOCK/OUT_OF_STOCK are no longer forwarded to the products API --
  // that filter now means "inventory-derived status", which the
  // products API has no way to check (see sortProducts.ts's own
  // docstring for the identical reasoning applied to sorting). Only
  // ARCHIVED/ALL (genuinely Product-owned state) go to the API; the
  // stock-status filter is applied client-side below, once inventory
  // data is in hand.
  const isStockStatusFilter = listFilter === "IN_STOCK" || listFilter === "OUT_OF_STOCK";
  const apiFilters = { listFilter: isStockStatusFilter ? "ALL" : listFilter, searchTerm: searchTerm || undefined };
  const { products, isLoading, isRefreshing, isError, refetch } = useProducts(apiFilters);

  // Inventory-derived status for each row -- see ProductCard's own
  // docstring for why this list fetches inventory itself rather than
  // ProductCard reading a legacy field on Product. Unfiltered fetch
  // (own cache entry, independent of this screen's search/filter) so
  // it doesn't refetch every keystroke.
  const { items: inventoryItems } = useInventoryList({});
  const statusByProductId = useMemo(() => {
    const map = new Map<string, (typeof inventoryItems)[number]["status"]>();
    for (const item of inventoryItems) map.set(item.product.id, item.status);
    return map;
  }, [inventoryItems]);

  const stockFilteredProducts = useMemo(() => {
    if (!isStockStatusFilter) return products;
    return products.filter((p) => statusByProductId.get(p.id) === listFilter);
  }, [products, isStockStatusFilter, listFilter, statusByProductId]);

  const sortedProducts = useMemo(
    () => sortProducts(stockFilteredProducts, sortOption, statusByProductId),
    [stockFilteredProducts, sortOption, statusByProductId]
  );

  // Recomputed locally rather than trusting useProducts' own
  // count/empty flags -- those are based on the API's response, which
  // no longer reflects the final list once a stock-status filter is
  // applied client-side on top of it.
  const productCount = sortedProducts.length;
  const hasActiveFilters = Boolean(searchTerm.trim()) || listFilter !== "ALL";
  const isEmpty = !isLoading && productCount === 0 && !hasActiveFilters;
  const isFilteredEmpty = !isLoading && productCount === 0 && hasActiveFilters;

  const goToAddProduct = () => router.push("/supplier/products/add");
  const goToProduct = (productId: string) => router.push(`/supplier/products/${productId}`);
  const clearFilters = () => {
    setSearchTerm("");
    setListFilter("ALL");
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await exportProducts();
    } catch {
      Alert.alert("Export failed", "Couldn't export your products. Check your connection and try again.");
    } finally {
      setIsExporting(false);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      await downloadImportTemplate();
    } catch {
      Alert.alert("Couldn't open the download", "Try again.");
    }
  };

  const handleDownloadGuide = async () => {
    try {
      await downloadImportGuide();
    } catch {
      Alert.alert("Couldn't open the download", "Try again.");
    }
  };

  // Header "⋮" menu -- set via navigation.setOptions rather than a
  // static Stack.Screen prop, since the menu's actions need to call
  // handlers defined here (export needs isExporting state, sort needs
  // to open sortSheetOpen). FeatureHeader reads options.headerRight
  // exactly like React Navigation's own header does.
  useLayoutEffect(() => {
    navigation.setOptions({
      headerRight: () => (
        <ProductsOverflowMenu
          onExport={handleExport}
          onSort={() => setSortSheetOpen(true)}
          onDownloadTemplate={handleDownloadTemplate}
          onDownloadGuide={handleDownloadGuide}
        />
      ),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigation]);

  if (isError) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load your products. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader paddingHorizontal={0}>
      {isExporting && (
        <View style={styles.exportingBanner}>
          <ActivityIndicator size="small" color={theme.colors.onPrimary} />
          <Text style={[styles.exportingText, { color: theme.colors.onPrimary }]}>Preparing export...</Text>
        </View>
      )}

      <FlatList<Product>
        data={sortedProducts}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={refetch} tintColor={theme.colors.primary} />
        }
        ListHeaderComponent={
          <View style={styles.header}>
            <View style={styles.countRow}>
              <Text style={[styles.count, { color: theme.colors.onSurfaceVariant }]}>
                {productCount === 1 ? "1 product" : `${productCount} products`}
              </Text>

              {/* Pure navigation shortcuts to Bulk Products -- NOT a
                  merge of the two features. No bulk-edit logic, state,
                  or components live here; these only ever router.push()
                  into ../../bulk-products' own routes. Same row as the
                  count (not a separate row) and no pill border, per
                  review -- compact icon+label, minimal footprint. */}
              <View style={styles.shortcutRow}>
                <Pressable
                  onPress={() => router.push("/supplier/bulk-products/import")}
                  style={styles.shortcutButton}
                  accessibilityRole="button"
                  accessibilityLabel="Bulk Upload"
                >
                  <UploadCloud size={17} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />
                  <Text style={[styles.shortcutLabel, { color: theme.colors.onSurfaceVariant }]}>Bulk Upload</Text>
                </Pressable>
                <Pressable
                  onPress={() => router.push("/supplier/bulk-products/edit")}
                  style={styles.shortcutButton}
                  accessibilityRole="button"
                  accessibilityLabel="Bulk Edit"
                >
                  <ListChecks size={17} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />
                  <Text style={[styles.shortcutLabel, { color: theme.colors.onSurfaceVariant }]}>Bulk Edit</Text>
                </Pressable>
              </View>
            </View>

            <ProductSearchBar value={searchTerm} onChangeText={setSearchTerm} onClear={() => setSearchTerm("")} />
            <ProductStatusFilterBar filter={listFilter} onFilterChange={setListFilter} />
          </View>
        }
        renderItem={({ item }) => (
          <ProductCard product={item} inventoryStatus={statusByProductId.get(item.id)} onPress={() => goToProduct(item.id)} />
        )}
        ItemSeparatorComponent={() => <View style={[styles.separator, { backgroundColor: theme.colors.outline }]} />}
        ListEmptyComponent={
          isLoading ? (
            <View style={styles.loading}>
              <ActivityIndicator color={theme.colors.primary} />
            </View>
          ) : isFilteredEmpty ? (
            <EmptyProducts variant="NO_RESULTS" onClearFilters={clearFilters} />
          ) : isEmpty ? (
            <EmptyProducts variant="FIRST_RUN" onAddProduct={goToAddProduct} />
          ) : null
        }
      />

      <Pressable
        onPress={goToAddProduct}
        style={[styles.fab, { backgroundColor: theme.colors.primary }]}
        accessibilityRole="button"
        accessibilityLabel="Add product"
      >
        <Plus size={26} color={theme.colors.onPrimary} strokeWidth={2.5} />
      </Pressable>

      <SortOptionsSheet
        visible={sortSheetOpen}
        selected={sortOption}
        onSelect={setSortOption}
        onClose={() => setSortSheetOpen(false)}
      />
    </ScreenContainer>
  );
}

const FAB_SIZE = 56;

const styles = StyleSheet.create({
  content: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    paddingBottom: spacing.xxl * 2,
    gap: spacing.sm,
  },
  header: { gap: spacing.md, marginBottom: spacing.sm },
  countRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  count: { ...typography.bodySmall },
  shortcutRow: { flexDirection: "row", gap: spacing.md },
  shortcutButton: { flexDirection: "row", alignItems: "center", gap: 5 },
  shortcutLabel: { ...typography.bodySmall, fontWeight: "700" },
  separator: { height: StyleSheet.hairlineWidth },
  loading: { paddingVertical: spacing.xxl, alignItems: "center" },
  exportingBanner: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    zIndex: 10,
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: spacing.sm,
    paddingVertical: spacing.xs,
    backgroundColor: "rgba(0,0,0,0.6)",
  },
  exportingText: { ...typography.bodySmall, fontWeight: "600" },
  fab: {
    position: "absolute",
    right: spacing.lg,
    bottom: spacing.lg,
    width: FAB_SIZE,
    height: FAB_SIZE,
    borderRadius: FAB_SIZE / 2,
    alignItems: "center",
    justifyContent: "center",
    elevation: 4,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
});
