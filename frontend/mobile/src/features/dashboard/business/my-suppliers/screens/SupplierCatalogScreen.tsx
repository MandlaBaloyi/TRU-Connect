import React, { useLayoutEffect, useRef, useState } from "react";
import { ActivityIndicator, Alert, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useNavigation, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Package, ShoppingCart } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { EmptyState } from "@/components/feedback/EmptyState";
import { ErrorState } from "@/components/feedback/ErrorState";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useSupplierProducts } from "../../find-supplier/hooks/useSupplierProducts";
import { useSupplierProductCategories } from "../../find-supplier/hooks/useSupplierProductCategories";
import { useEndConnection } from "../../find-supplier/hooks/useEndConnection";
import { useReportSupplier } from "../../find-supplier/hooks/useReportSupplier";
import { useCart } from "../../orders/hooks/useCart";
import { SupplierCatalogProductCard } from "../components/SupplierCatalogProductCard";
import { CatalogControlsRow } from "../components/CatalogControlsRow";
import { CatalogSortSheet } from "../components/CatalogSortSheet";
import { CatalogCategoryFilterSheet } from "../components/CatalogCategoryFilterSheet";
import { CatalogPager } from "../components/CatalogPager";
import { SupplierCatalogMenu } from "../components/SupplierCatalogMenu";
import { ContactSupplierSheet } from "../components/ContactSupplierSheet";
import { ReportSupplierSheet } from "../components/ReportSupplierSheet";
import { DisconnectSupplierSheet } from "../components/DisconnectSupplierSheet";
import type { DisconnectReason, ReportReason, SupplierProduct } from "../../find-supplier/types";
import type { CatalogCategoryFilter, CatalogSortOption } from "../types";

/**
 * A connected (or merely browsable -- see this hook's own docstring
 * on why browsing stays open regardless of connection status) supplier's
 * real catalogue -- real photos, real prices, the same "% OFF" badge
 * the supplier sees on their own product screens.
 *
 * supplierName IS THE REAL "CERTAINTY" FIX, applied here one screen
 * earlier than the product detail screen's own version of it.
 *
 * SORT/FILTER/PAGINATION ARE ALL GENUINELY SERVER-SIDE. The category
 * filter's own OPTIONS come from useSupplierProductCategories -- a
 * real, dedicated backend query, fetched once, correct regardless of
 * which page/sort/filter is currently active. This used to be derived
 * from whichever products happened to be loaded, which broke the
 * moment pagination existed (the option list would shift depending on
 * which page you were on) -- a real bug found during review, fixed at
 * the actual source rather than patched around.
 *
 * A CHANGED SORT OR FILTER RESETS BACK TO PAGE 1 -- staying on page 3
 * of a now-different result set could land past its real end.
 *
 * THE STICKY-SCROLL DUPLICATE BUG, FOUND AND FIXED: changing pages
 * used to leave the scroll position wherever it was on the OLD page,
 * so a scroll offset from partway down page 1 would carry over onto
 * page 2's fresh content -- comparing that stale offset against the
 * controls row's own position could show BOTH the pinned copy and the
 * inline one at once. Fixed by explicitly scrolling back to the top
 * (and resetting the tracked scrollY) every time the page changes --
 * which is also just the right behaviour on its own: a new page
 * should open at its own top, not wherever you happened to be
 * scrolled on the last one.
 */
export default function SupplierCatalogScreen() {
  const { supplierId } = useLocalSearchParams<{ supplierId: string }>();
  const router = useRouter();
  const navigation = useNavigation();
  const theme = useTheme();
  const flatListRef = useRef<FlatList<SupplierProduct>>(null);

  const [page, setPage] = useState(1);
  const [sortOption, setSortOption] = useState<CatalogSortOption>("NEWEST");
  const [categoryFilter, setCategoryFilter] = useState<CatalogCategoryFilter>(null);

  const { supplierName, contact, products, totalPages, totalCount, isLoading, isError, refetch } =
    useSupplierProducts(supplierId ?? "", {
      page,
      sort: sortOption,
      category: categoryFilter,
    });
  const { categories: availableCategories } = useSupplierProductCategories(supplierId ?? "");
  const { endConnection, isEnding } = useEndConnection(supplierId ?? "");
  const { reportSupplier, isReporting } = useReportSupplier(supplierId ?? "");
  const { cart } = useCart(supplierId ?? "");
  const cartItemCount = cart?.itemCount ?? 0;

  const [sortSheetOpen, setSortSheetOpen] = useState(false);
  const [filterSheetOpen, setFilterSheetOpen] = useState(false);
  const [contactSheetOpen, setContactSheetOpen] = useState(false);
  const [reportSheetOpen, setReportSheetOpen] = useState(false);
  const [disconnectSheetOpen, setDisconnectSheetOpen] = useState(false);

  const [scrollY, setScrollY] = useState(0);
  const [controlsRowY, setControlsRowY] = useState<number | null>(null);
  const isSticky = controlsRowY !== null && scrollY >= controlsRowY;

  // THE REAL FIX for the sticky-header duplicate bug -- see this
  // screen's own docstring for the full trace. Every page change
  // resets the scroll position to the top, both physically
  // (scrollToOffset) and in the state this sticky calculation reads
  // from (scrollY) -- without resetting BOTH, a stale scrollY could
  // still momentarily read as "past the controls row" even after the
  // list itself visually snaps back up.
  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    setScrollY(0);
    flatListRef.current?.scrollToOffset({ offset: 0, animated: false });
  };

  const handleSortChange = (option: CatalogSortOption) => {
    setSortOption(option);
    handlePageChange(1);
  };

  const handleCategoryChange = (category: CatalogCategoryFilter) => {
    setCategoryFilter(category);
    handlePageChange(1);
  };

  const handleReport = async (reason: ReportReason, details: string | null) => {
    try {
      await reportSupplier({ reason, details });
      setReportSheetOpen(false);
      Alert.alert("Report submitted", "Thanks for letting us know. Our team will review this.");
    } catch {
      Alert.alert("Couldn't submit report", "Check your connection and try again.");
    }
  };

  const handleDisconnect = async (reason: DisconnectReason, details: string | null) => {
    try {
      await endConnection({ reason, details });
      setDisconnectSheetOpen(false);
      router.back();
    } catch {
      Alert.alert("Couldn't disconnect", "Check your connection and try again.");
    }
  };

  // Header "⋮" menu -- set via navigation.setOptions rather than a
  // static Stack.Screen prop, same established reasoning as
  // ProductsScreen.tsx's own identical comment: the menu's actions
  // need to call handlers/state defined here.
  useLayoutEffect(() => {
    navigation.setOptions({
      headerRight: () => (
        <View style={styles.headerRightRow}>
          <Pressable
            onPress={() => router.push(`/business/orders/${supplierId}` as any)}
            hitSlop={10}
            style={styles.cartButton}
            accessibilityRole="button"
            accessibilityLabel="Cart"
          >
            <ShoppingCart size={20} color={theme.colors.onSurface} strokeWidth={2.2} />
            {cartItemCount > 0 && (
              <View style={[styles.cartBadge, { backgroundColor: theme.colors.error }]}>
                <Text style={styles.cartBadgeText}>{cartItemCount > 9 ? "9+" : cartItemCount}</Text>
              </View>
            )}
          </Pressable>
          <SupplierCatalogMenu
            onViewProfile={() => router.push(`/business/find-supplier/${supplierId}` as any)}
            onContactSupplier={() => setContactSheetOpen(true)}
            onReport={() => setReportSheetOpen(true)}
            onDisconnect={() => setDisconnectSheetOpen(true)}
          />
        </View>
      ),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigation, supplierId, cartItemCount]);

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load this supplier's products. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  if (totalCount === 0) {
    return (
      <ScreenContainer hasNativeHeader>
        <EmptyState
          icon={<Package size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
          message={
            supplierName ? `${supplierName} hasn't listed any products yet.` : "This supplier hasn't listed any products yet."
          }
        />
      </ScreenContainer>
    );
  }

  const controlsRow = (
    <CatalogControlsRow
      itemCount={totalCount}
      filterActive={categoryFilter !== null}
      onPressSort={() => setSortSheetOpen(true)}
      onPressFilter={() => setFilterSheetOpen(true)}
    />
  );

  return (
    <ScreenContainer hasNativeHeader>
      {isSticky && (
        <View style={[styles.pinned, { backgroundColor: theme.colors.background, borderBottomColor: theme.colors.outlineVariant }]}>
          {controlsRow}
        </View>
      )}
      <FlatList
        ref={flatListRef}
        data={products}
        keyExtractor={(product) => product.id}
        numColumns={2}
        columnWrapperStyle={styles.row}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        onScroll={(event) => setScrollY(event.nativeEvent.contentOffset.y)}
        scrollEventThrottle={16}
        ListHeaderComponent={
          <View>
            {supplierName && (
              <Text style={[styles.supplierName, { color: theme.colors.onSurface }]}>{supplierName}</Text>
            )}
            <View onLayout={(event) => setControlsRowY(event.nativeEvent.layout.y)}>{controlsRow}</View>
          </View>
        }
        ListEmptyComponent={
          <Text style={[styles.noMatches, { color: theme.colors.onSurfaceVariant }]}>
            No products match this filter.
          </Text>
        }
        ListFooterComponent={<CatalogPager page={page} totalPages={totalPages} onPageChange={handlePageChange} />}
        renderItem={({ item }) => (
          <SupplierCatalogProductCard
            product={item}
            onPress={() => router.push(`/business/my-suppliers/${supplierId}/products/${item.id}` as any)}
          />
        )}
      />

      <CatalogSortSheet
        visible={sortSheetOpen}
        selected={sortOption}
        onSelect={handleSortChange}
        onClose={() => setSortSheetOpen(false)}
      />
      <CatalogCategoryFilterSheet
        visible={filterSheetOpen}
        availableCategories={availableCategories}
        selected={categoryFilter}
        onSelect={handleCategoryChange}
        onClose={() => setFilterSheetOpen(false)}
      />
      <ContactSupplierSheet
        visible={contactSheetOpen}
        supplierName={supplierName ?? "this supplier"}
        contact={contact}
        onClose={() => setContactSheetOpen(false)}
      />
      <ReportSupplierSheet
        visible={reportSheetOpen}
        supplierName={supplierName ?? "this supplier"}
        isSubmitting={isReporting}
        onSubmit={handleReport}
        onClose={() => setReportSheetOpen(false)}
      />
      <DisconnectSupplierSheet
        visible={disconnectSheetOpen}
        supplierName={supplierName ?? "this supplier"}
        isSubmitting={isEnding}
        onSubmit={handleDisconnect}
        onClose={() => setDisconnectSheetOpen(false)}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  headerRightRow: { flexDirection: "row", alignItems: "center" },
  cartButton: { padding: spacing.xs, position: "relative" },
  cartBadge: {
    position: "absolute",
    top: 0,
    right: 0,
    minWidth: 16,
    height: 16,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 3,
  },
  cartBadgeText: { color: "#FFFFFF", fontSize: 10, fontWeight: "700" },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  list: { padding: spacing.md, gap: spacing.md },
  row: { justifyContent: "space-between" },
  supplierName: { ...typography.h1, marginBottom: spacing.sm },
  noMatches: { ...typography.body, textAlign: "center", paddingTop: spacing.xl },
  pinned: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    zIndex: 10,
    paddingHorizontal: spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
});
