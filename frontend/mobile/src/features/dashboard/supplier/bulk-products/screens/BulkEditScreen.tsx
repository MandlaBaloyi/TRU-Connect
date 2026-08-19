/**
 * BulkEditScreen — one of Bulk Products' two entry points ("Bulk
 * Edit"), reached directly from the Products screen's own "Bulk Edit"
 * shortcut. Same standing as Order Book/Loan Book each having their
 * own screen rather than being modes bolted onto another feature's
 * screen. Products (1-50 items) stays a simple one-at-a-time tool;
 * this screen exists for mass Change Price / Archive across EXISTING
 * products at once.
 *
 * "UPDATE STOCK" WAS RETIRED FROM THIS SCREEN -- once Products
 * migrated to inventory-derived status (see ProductCard's own
 * docstring), bulk-setting Product.stockStatus stopped having any
 * visible effect anywhere -- the button would have kept working while
 * silently doing nothing a supplier could see, which is worse than
 * not offering it. A real "Bulk Inventory" (mass stock ADJUSTMENT,
 * matching Inventory's own Adjust Stock design, not a binary status
 * toggle) is the natural replacement, flagged as a follow-up, not
 * built here.
 *
 * NOT the "publish a whole spreadsheet of new stock" feature -- that's
 * Import Products (ImportUploadScreen/ImportPreviewScreen). Bulk Edit
 * only ever touches products that already exist; Import Products
 * creates new ones.
 *
 * EVERY ROW IS SELECTABLE FROM THE MOMENT YOU LAND HERE -- no
 * long-press needed. This screen's whole reason to exist is selection,
 * so selection is just how it always looks.
 *
 * Reuses products/hooks (useProducts) and products/components
 * (ProductCard, search/filter bars) directly -- this is the SAME
 * underlying product data and the SAME visual language, not a
 * duplicate list rebuilt from scratch. Also fetches inventory data
 * (useInventoryList) for the same reason ProductsScreen does now --
 * ProductCard's badge comes from the caller, not from Product itself.
 */

import React, { useMemo, useState } from "react";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { useProducts } from "../../products/hooks";
import { EmptyProducts, ProductCard, ProductSearchBar, ProductStatusFilterBar } from "../../products/components";
import type { Product, ProductListFilter } from "../../products/types";
import { useBulkProductActions } from "../hooks";
import type { PriceAdjustment } from "../types";
import { BulkPriceModal, SelectionActionBar } from "../components";
import { useInventoryList } from "../../inventory/hooks";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

export default function BulkEditScreen() {
  const theme = useTheme();

  const [searchTerm, setSearchTerm] = useState("");
  const [listFilter, setListFilter] = useState<ProductListFilter>("ALL");
  const filters = { listFilter, searchTerm: searchTerm || undefined };
  const { products, productCount, isLoading, isError, isEmpty, isFilteredEmpty, refetch } = useProducts(filters);

  const { items: inventoryItems } = useInventoryList({});
  const statusByProductId = useMemo(() => {
    const map = new Map<string, (typeof inventoryItems)[number]["status"]>();
    for (const item of inventoryItems) map.set(item.product.id, item.status);
    return map;
  }, [inventoryItems]);

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [priceModalOpen, setPriceModalOpen] = useState(false);
  const { bulkAdjustPrice, isBulkAdjustingPrice, bulkArchive } = useBulkProductActions();

  const toggleSelected = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };
  const selectAllVisible = () => setSelectedIds(new Set(products.map((p) => p.id)));
  const clearSelection = () => setSelectedIds(new Set());

  const selectedProducts = products.filter((p) => selectedIds.has(p.id));
  const showArchiveAction = selectedProducts.some((p) => !p.isArchived);
  const allVisibleSelected = products.length > 0 && selectedIds.size === products.length;

  const handleApplyPrice = async (adjustment: PriceAdjustment) => {
    await bulkAdjustPrice({ productIds: Array.from(selectedIds), adjustment });
    setPriceModalOpen(false);
    clearSelection();
  };

  const handleArchive = async () => {
    await bulkArchive(Array.from(selectedIds));
    clearSelection();
  };

  if (isError) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load your products. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader paddingHorizontal={0}>
      <FlatList<Product>
        data={products}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.content}
        ListHeaderComponent={
          <View style={styles.header}>
            <Text style={[styles.intro, { color: theme.colors.onSurfaceVariant }]}>
              Select products to change price or archive many at once.
            </Text>
            <View style={styles.countRow}>
              <Text style={[styles.count, { color: theme.colors.onSurfaceVariant }]}>
                {productCount === 1 ? "1 product" : `${productCount} products`}
              </Text>
              <Pressable
                onPress={allVisibleSelected ? clearSelection : selectAllVisible}
                accessibilityRole="button"
                accessibilityLabel={allVisibleSelected ? "Clear selection" : "Select all"}
              >
                <Text style={[styles.selectAll, { color: theme.colors.primary }]}>
                  {allVisibleSelected ? "Clear selection" : "Select all"}
                </Text>
              </Pressable>
            </View>
            <ProductSearchBar value={searchTerm} onChangeText={setSearchTerm} onClear={() => setSearchTerm("")} />
            <ProductStatusFilterBar filter={listFilter} onFilterChange={setListFilter} />
          </View>
        }
        renderItem={({ item }) => (
          <ProductCard
            product={item}
            inventoryStatus={statusByProductId.get(item.id)}
            selectable
            selected={selectedIds.has(item.id)}
            onPress={() => toggleSelected(item.id)}
          />
        )}
        ItemSeparatorComponent={() => <View style={[styles.separator, { backgroundColor: theme.colors.outline }]} />}
        ListEmptyComponent={
          isLoading ? (
            <View style={styles.loading}>
              <ActivityIndicator color={theme.colors.primary} />
            </View>
          ) : isFilteredEmpty ? (
            <EmptyProducts
              variant="NO_RESULTS"
              onClearFilters={() => {
                setSearchTerm("");
                setListFilter("ALL");
              }}
            />
          ) : isEmpty ? (
            <EmptyProducts variant="FIRST_RUN" />
          ) : null
        }
      />

      {selectedIds.size > 0 && (
        <SelectionActionBar
          selectedCount={selectedIds.size}
          showArchiveAction={showArchiveAction}
          onChangePrice={() => setPriceModalOpen(true)}
          onArchive={handleArchive}
          onCancel={clearSelection}
        />
      )}

      <BulkPriceModal
        visible={priceModalOpen}
        selectedCount={selectedIds.size}
        isSubmitting={isBulkAdjustingPrice}
        onApply={handleApplyPrice}
        onClose={() => setPriceModalOpen(false)}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    paddingBottom: spacing.xxl * 2,
    gap: spacing.sm,
  },
  header: { gap: spacing.md, marginBottom: spacing.sm },
  intro: { ...typography.bodySmall },
  countRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  count: { ...typography.bodySmall },
  selectAll: { ...typography.bodySmall, fontWeight: "700" },
  separator: { height: StyleSheet.hairlineWidth },
  loading: { paddingVertical: spacing.xxl, alignItems: "center" },
});
