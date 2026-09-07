import React, { useEffect, useLayoutEffect, useRef, useState } from "react";
import { ActivityIndicator, Alert, FlatList, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useLocalSearchParams, useNavigation, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Package, Search, ShoppingCart, X } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { EmptyState } from "@/components/feedback/EmptyState";
import { ErrorState } from "@/components/feedback/ErrorState";
import { EntityHeaderTitle } from "@/components/navigation/EntityHeaderTitle";
import { showsAsVerified } from "@/constants/config";
import { productDetailHref, supplierProfileHref } from "../../routes";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { CATEGORY_OPTIONS } from "../../../supplier/products/types";
import { useSupplierProducts } from "../../find-supplier/hooks/useSupplierProducts";
import { useSupplierProductCategories } from "../../find-supplier/hooks/useSupplierProductCategories";
import { useEndConnection } from "../../find-supplier/hooks/useEndConnection";
import { useReportSupplier } from "../../find-supplier/hooks/useReportSupplier";
import { useCart } from "../../orders/hooks/useCart";
import { useAddToCart } from "../../orders/hooks/useAddToCart";
import { ApiError } from "@/services/api/apiClient";
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
  const { supplierId, category, supplierName: supplierNameParam } = useLocalSearchParams<{
    supplierId: string;
    category?: string;
    supplierName?: string;
  }>();
  const router = useRouter();
  const navigation = useNavigation();
  const theme = useTheme();
  const flatListRef = useRef<FlatList<SupplierProduct>>(null);

  // "See all in <category>" from the brand profile lands here already
  // filtered -- but only trust a value that's a real TruConnect
  // category, never whatever a deep link happens to carry.
  const initialCategory: CatalogCategoryFilter =
    category && CATEGORY_OPTIONS.some((o) => o.value === category) ? category : null;

  const [page, setPage] = useState(1);
  const [sortOption, setSortOption] = useState<CatalogSortOption>("RECOMMENDED");
  const [categoryFilter, setCategoryFilter] = useState<CatalogCategoryFilter>(initialCategory);
  // Typed value vs the value actually SENT. Firing a request per
  // keystroke would put a round trip behind every letter; the debounce
  // below settles it. Both live here so the input stays responsive
  // while the query lags behind it.
  const [searchInput, setSearchInput] = useState("");
  const [searchTerm, setSearchTerm] = useState("");

  // 350ms: long enough that "coca-cola" is one request rather than
  // nine, short enough that it still feels like live search.
  useEffect(() => {
    const timer = setTimeout(() => setSearchTerm(searchInput.trim()), 350);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // A new search is a new result set, so page 3 of the old one is
  // meaningless -- same reasoning as handleSortChange below.
  useEffect(() => {
    setPage(1);
  }, [searchTerm]);

  const {
    supplierName,
    supplierBusinessImageUrl,
    supplierVerificationStatus,
    contact,
    products,
    totalPages,
    totalCount,
    isLoading,
    isError,
    refetch,
  } = useSupplierProducts(supplierId ?? "", {
    page,
    sort: sortOption,
    category: categoryFilter,
    search: searchTerm || null,
  });
  // THE HEADER FLASH FIX, reported directly: opening this screen cold
  // showed "Stock Catalogue" for a beat and then swapped to the real
  // supplier name, because the title could only become real once the
  // products request resolved. Every caller ALREADY knows the name
  // when it navigates here (My Connections has connection.name, the
  // brand profile has supplier.businessName), so it's passed through
  // as a route param and read synchronously -- the exact same fix, for
  // the exact same class of bug, that create-account.tsx documents in
  // its own docstring (point 6: re-fetching a value the caller already
  // had in hand is what produced the visible gap). The fetched name
  // still wins once it arrives, so a stale/absent param self-corrects
  // rather than sticking.
  const headerSupplierName = supplierName ?? supplierNameParam ?? null;

  const { categories: availableCategories } = useSupplierProductCategories(supplierId ?? "");
  const { endConnection, isEnding } = useEndConnection(supplierId ?? "");
  const { reportSupplier, isReporting } = useReportSupplier(supplierId ?? "");
  const { cart } = useCart(supplierId ?? "");
  const { addToCart } = useAddToCart(supplierId ?? "");
  // Which card is mid-request, so only THAT button shows "Adding…"
  // rather than every card on the page going busy at once.
  const [addingProductId, setAddingProductId] = useState<string | null>(null);
  const cartItemCount = cart?.itemCount ?? 0;

  const [sortSheetOpen, setSortSheetOpen] = useState(false);
  const [filterSheetOpen, setFilterSheetOpen] = useState(false);
  const [contactSheetOpen, setContactSheetOpen] = useState(false);
  const [reportSheetOpen, setReportSheetOpen] = useState(false);
  const [disconnectSheetOpen, setDisconnectSheetOpen] = useState(false);

  const [scrollY, setScrollY] = useState(0);
  const [controlsRowY, setControlsRowY] = useState<number | null>(null);
  // STRICTLY GREATER THAN, not >=. This used to be >=, which was
  // correct only while the supplier's name sat above the controls row
  // in the list header (so controlsRowY was always a positive offset).
  // Once the name moved up into the top bar (EntityHeaderTitle), the
  // controls row became the FIRST thing in the header -- controlsRowY
  // is now 0, so `scrollY >= 0` was true at rest and the pinned copy
  // rendered on top of the inline one permanently: two identical
  // "26 items / Sort / Filter" rows, visible without scrolling at all.
  // `>` is the honest test either way -- "have we actually scrolled
  // past it", which at offset 0 we plainly have not.
  const isSticky = controlsRowY !== null && scrollY > controlsRowY;

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

  const handleAddToCart = async (product: SupplierProduct) => {
    setAddingProductId(product.id);
    try {
      await addToCart({ productId: product.id, quantity: 1 });
    } catch (error) {
      // The backend names the exact product in its out-of-stock
      // message, so it's shown as-is rather than reworded.
      if (error instanceof ApiError && error.code === "OUT_OF_STOCK") {
        Alert.alert("Out of stock", error.message);
      } else {
        Alert.alert("Couldn't add to cart", "Check your connection and try again.");
      }
    } finally {
      setAddingProductId(null);
    }
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
      // Social-style top bar: the supplier's avatar + business name,
      // with "Stock catalogue" as the quiet second line, so a business
      // is certain whose stock this is. Two lines rather than one
      // "<name> Stock" string -- see EntityHeaderTitle's own docstring
      // on why that truncated the name away. Falls back to the
      // _layout.tsx "Stock Catalogue" string while still loading.
      ...(headerSupplierName
        ? {
            headerTitle: () => (
              <EntityHeaderTitle
                name={headerSupplierName}
                subtitle="Stock catalogue"
                photoUrl={supplierBusinessImageUrl}
                verified={showsAsVerified(supplierVerificationStatus)}
                onPress={() => router.push(supplierProfileHref(supplierId, headerSupplierName) as any)}
              />
            ),
          }
        : {}),
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
            onViewProfile={() => router.push(supplierProfileHref(supplierId, headerSupplierName) as any)}
            onContactSupplier={() => setContactSheetOpen(true)}
            onReport={() => setReportSheetOpen(true)}
            onDisconnect={() => setDisconnectSheetOpen(true)}
          />
        </View>
      ),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigation, supplierId, cartItemCount, headerSupplierName, supplierBusinessImageUrl, supplierVerificationStatus]);

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

  // ONLY when the supplier genuinely has nothing -- a search or filter
  // that matches nothing also returns totalCount 0, and telling a
  // business "this supplier hasn't listed any products" because they
  // typed "xyz" would be a flat lie. Those cases fall through to the
  // list's own "nothing matches" empty state, which keeps the search
  // bar on screen so the term can be corrected.
  if (totalCount === 0 && !searchTerm && !categoryFilter) {
    return (
      <ScreenContainer hasNativeHeader>
        <EmptyState
          icon={<Package size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
          message={
            headerSupplierName
              ? `${headerSupplierName} hasn't listed any products yet.`
              : "This supplier hasn't listed any products yet."
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
          // The supplier's name now lives in the top bar
          // (EntityHeaderTitle), so it's no longer repeated here.
          <View>
            {/* SEARCH INSIDE THIS SUPPLIER'S CATALOGUE. At 26 products
                you can scroll; at 300 the only way to find one item was
                guessing its category. Server-side (before pagination) --
                a client-side filter could only ever search the page you
                happen to be on. */}
            <View style={[styles.searchWrap, { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface }]}>
              <Search size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
              <TextInput
                value={searchInput}
                onChangeText={setSearchInput}
                placeholder="Search this catalogue"
                placeholderTextColor={theme.colors.onSurfaceVariant}
                style={[styles.searchInput, { color: theme.colors.onSurface }]}
                autoCapitalize="none"
                autoCorrect={false}
                returnKeyType="search"
                accessibilityLabel="Search this catalogue"
              />
              {searchInput.length > 0 && (
                <Pressable
                  onPress={() => setSearchInput("")}
                  hitSlop={10}
                  accessibilityRole="button"
                  accessibilityLabel="Clear search"
                >
                  <X size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />
                </Pressable>
              )}
            </View>
            <View onLayout={(event) => setControlsRowY(event.nativeEvent.layout.y)}>{controlsRow}</View>
          </View>
        }
        ListEmptyComponent={
          <Text style={[styles.noMatches, { color: theme.colors.onSurfaceVariant }]}>
            {searchTerm
              ? `Nothing matches "${searchTerm}" in this catalogue.`
              : "No products match this filter."}
          </Text>
        }
        ListFooterComponent={<CatalogPager page={page} totalPages={totalPages} onPageChange={handlePageChange} />}
        renderItem={({ item }) => (
          <SupplierCatalogProductCard
            product={item}
            onPress={() => router.push(productDetailHref(supplierId, item.id, item.name, headerSupplierName) as any)}
            onAddToCart={() => handleAddToCart(item)}
            isAdding={addingProductId === item.id}
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
  searchWrap: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    borderWidth: 1,
    borderRadius: 24,
    marginBottom: spacing.sm,
  },
  searchInput: { flex: 1, ...typography.body, paddingVertical: 10 },
  list: { padding: spacing.md, gap: spacing.md },
  row: { justifyContent: "space-between" },
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
