/**
 * InventoryScreen — "how much of each product can I currently sell?"
 * Own Account tile, own routes -- not inside Products, per direct
 * instruction. Compact vertical list, same discipline as Products'
 * own list screen: search is local/instant, filter chips are a single
 * scrollable row, no charts, just four honest counts at the top.
 *
 * The "⋮" menu's two settings items open BOTTOM-SHEET MODALS, not
 * navigated screens -- per direct review: "the way it appears is not
 * screen but is clean, simple, easy" -- matching Products' own Sort by
 * exactly (products/components/SortOptionsSheet.tsx): tap an option,
 * it applies and the sheet closes immediately.
 *
 * BUG FIX: these two sheets were previously gated behind
 * `{settings && (...)}`, unlike Sort by's own SortOptionsSheet (which
 * reads plain synchronous local state and is always mounted). Since
 * `settings` comes from an async fetch, that gate meant the sheets
 * genuinely didn't exist in the tree yet if a tap landed before the
 * fetch resolved -- so `visible={true}` had nothing to apply to, and
 * the menu item appeared to do nothing. Fixed by always rendering both
 * sheets and falling back to the same defaults mockInventoryApi.ts
 * itself seeds (5, "IN_APP") while settings is still loading.
 */

import React, { useLayoutEffect, useState } from "react";
import { ActivityIndicator, Alert, FlatList, RefreshControl, StyleSheet, View } from "react-native";
import { useNavigation, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { useInventoryList, useInventorySettings, useInventorySummary } from "../hooks";
import type { InventoryFilter, InventoryListItem, LowStockAlertChannel } from "../types";
import {
  DefaultThresholdSheet,
  EmptyInventory,
  InventoryFilterBar,
  InventoryListRow,
  InventoryOverflowMenu,
  InventorySummaryBar,
  LowStockAlertSheet,
} from "../components";
import { exportInventory } from "../services/exportInventory";
import { ProductSearchBar } from "../../products/components";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { spacing } from "@/theme/spacing";

export default function InventoryScreen() {
  const router = useRouter();
  const navigation = useNavigation();
  const theme = useTheme();

  const [searchTerm, setSearchTerm] = useState("");
  const [filter, setFilter] = useState<InventoryFilter>("ALL");
  const [isExporting, setIsExporting] = useState(false);
  const [thresholdSheetOpen, setThresholdSheetOpen] = useState(false);
  const [alertSheetOpen, setAlertSheetOpen] = useState(false);

  const filters = { filter, searchTerm: searchTerm || undefined };
  const { items, isLoading, isRefreshing, isError, isEmpty, isFilteredEmpty, refetch } = useInventoryList(filters);
  const { summary } = useInventorySummary();
  const { settings, updateSettings, isUpdating } = useInventorySettings();

  const goToDetail = (productId: string) => router.push(`/supplier/inventory/${productId}`);
  const clearFilters = () => {
    setSearchTerm("");
    setFilter("ALL");
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await exportInventory();
    } catch {
      Alert.alert("Export failed", "Couldn't export your inventory. Check your connection and try again.");
    } finally {
      setIsExporting(false);
    }
  };

  const handleApplyThreshold = (value: number) => {
    updateSettings({ defaultLowStockThreshold: value });
  };

  const handleApplyAlertChannel = (channel: LowStockAlertChannel) => {
    updateSettings({ lowStockAlertChannel: channel });
  };

  // Header "⋮" menu -- same navigation.setOptions pattern as Products'
  // own ProductsScreen. Export needs local state (isExporting); the
  // two settings open their own bottom sheets, same local-state pattern
  // Products uses for its own Sort by sheet.
  useLayoutEffect(() => {
    navigation.setOptions({
      headerRight: () => (
        <InventoryOverflowMenu
          onExport={handleExport}
          onEditDefaultThreshold={() => setThresholdSheetOpen(true)}
          onEditAlertChannel={() => setAlertSheetOpen(true)}
        />
      ),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigation]);

  if (isError) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load your inventory. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader paddingHorizontal={0}>
      {isExporting && (
        <View style={styles.exportingBanner}>
          <ActivityIndicator size="small" color={theme.colors.onPrimary} />
        </View>
      )}

      <FlatList<InventoryListItem>
        data={items}
        keyExtractor={(item) => item.product.id}
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={refetch} tintColor={theme.colors.primary} />
        }
        ListHeaderComponent={
          <View style={styles.header}>
            {summary && <InventorySummaryBar summary={summary} />}
            <ProductSearchBar value={searchTerm} onChangeText={setSearchTerm} onClear={() => setSearchTerm("")} />
            <InventoryFilterBar filter={filter} onFilterChange={setFilter} />
          </View>
        }
        renderItem={({ item }) => <InventoryListRow item={item} onPress={() => goToDetail(item.product.id)} />}
        ItemSeparatorComponent={() => <View style={[styles.separator, { backgroundColor: theme.colors.outline }]} />}
        ListEmptyComponent={
          isLoading ? (
            <View style={styles.loading}>
              <ActivityIndicator color={theme.colors.primary} />
            </View>
          ) : isFilteredEmpty ? (
            <EmptyInventory variant="NO_RESULTS" onClearFilters={clearFilters} />
          ) : isEmpty ? (
            <EmptyInventory variant="FIRST_RUN" />
          ) : null
        }
      />

      <DefaultThresholdSheet
        visible={thresholdSheetOpen}
        currentValue={settings?.defaultLowStockThreshold ?? 5}
        isSubmitting={isUpdating}
        onApply={handleApplyThreshold}
        onClose={() => setThresholdSheetOpen(false)}
      />
      <LowStockAlertSheet
        visible={alertSheetOpen}
        selected={settings?.lowStockAlertChannel ?? "IN_APP"}
        onSelect={handleApplyAlertChannel}
        onClose={() => setAlertSheetOpen(false)}
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
  separator: { height: StyleSheet.hairlineWidth },
  loading: { paddingVertical: spacing.xxl, alignItems: "center" },
  exportingBanner: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    zIndex: 10,
    alignItems: "center",
    paddingVertical: spacing.xs,
    backgroundColor: "rgba(0,0,0,0.6)",
  },
});
