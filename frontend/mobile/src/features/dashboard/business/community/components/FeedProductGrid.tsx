import React from "react";
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { ErrorState } from "@/components/feedback/ErrorState";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { BrowseFilterBar } from "@/features/dashboard/business/browse/components/BrowseFilterBar";
import { BrowseHeader } from "@/features/dashboard/business/browse/components/BrowseHeader";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { productDetailHref } from "../../routes";
import { ProductTile } from "./cards/ProductTile";
import type { FeedProduct } from "../types";

const COLUMNS = 2;

/** The orderings a see-all offers. RELEVANCE IS FIRST AND IS THE
 *  DEFAULT, and it means "leave the order alone": every one of these
 *  lists arrives ranked by something that took real work -- most
 *  recently ordered, most tapped, fastest rising -- and that ranking is
 *  the rail's whole argument for existing. A screen that silently
 *  alphabetised it would throw away the reason the reader tapped
 *  through the arrow. */
const SEE_ALL_SORTS = [
  { value: "relevance" as const, label: "Best match", hint: "The order this list is ranked in" },
  { value: "price_asc" as const, label: "Cheapest first", hint: "Lowest price first" },
  { value: "price_desc" as const, label: "Most expensive first", hint: "Highest price first" },
  { value: "name" as const, label: "A–Z", hint: "Alphabetical" },
];

/**
 * The screen behind every product rail's arrow.
 *
 * ONE SCREEN SHAPE FOR FOUR DESTINATIONS. Reorder what you need,
 * Continue stocking up, Popular with businesses and Stock for your shop
 * differ only in their title and their query; four screen files would
 * have been four chances to disagree about empty states, paging and
 * pull-to-refresh.
 *
 * IT NOW CARRIES THE CATEGORY BROWSE'S CONTROLS, because it has the
 * same problem. "Reorder what you need" for a shop with a hundred lines
 * is the browse's thousand-product scroll in miniature, and the answer
 * is the same: let them narrow rather than asking them to scroll. Same
 * header, same filter bar, same sheet -- a shopkeeper should not have
 * to learn two ways to find something.
 *
 * TWO COLUMNS, AND THAT REVERSES A DOCUMENTED DECISION. This grid was
 * three across, argued on the grounds that "a rail is a preview you
 * glance along, a screen is a catalogue you search with your eyes. Two
 * columns wastes the width". The argument was reasonable and the pixels
 * disagreed: at three across on a 360pt handset each tile is about
 * 105pt, and a real screenshot showed "Giyani General ..." , "MacMan
 * Busine..." and "Bought by 1 busi..." -- the supplier name and the
 * social proof, which are two of the three reasons the card exists,
 * both truncated on most cards. A denser grid that cannot say who is
 * selling is not denser, it is emptier.
 *
 * THE SAME ProductTile THE RAILS USE, at a width the grid computes. A
 * second card component would have drifted -- the tile carries the
 * supplier's name, the verification tick, the saving pill, the
 * out-of-stock scrim and the "Bought by N businesses" line, and every
 * one of those would eventually have been fixed in one place only.
 */
export function FeedProductGrid({
  title,
  feed,
  emptyTitle,
  emptyBody,
}: {
  title: string;
  /** The whole useFeedProducts result. Passed wholesale rather than as
   *  fifteen props: the hook owns the filters precisely so the screen
   *  and the query cannot disagree, and unpacking it here would put
   *  half of that state back in the caller. */
  feed: {
    products: FeedProduct[];
    total: number | null;
    suppliers: { id: string; name: string; count: number }[];
    controls: { search?: string; sort?: string; supplier?: string | null };
    setSearch: (value: string) => void;
    toggleSupplier: (id: string) => void;
    setSort: (value: any) => void;
    isLoading: boolean;
    isError: boolean;
    refetch: () => void;
    isRefetching: boolean;
    fetchNextPage: () => void;
    hasNextPage?: boolean;
    isFetchingNextPage: boolean;
  };
  emptyTitle: string;
  emptyBody: string;
}) {
  const theme = useTheme();
  const router = useRouter();

  const { controls } = feed;
  const narrowed = Boolean(controls.search || controls.supplier);

  // A TRAILING SPACER WHEN THE COUNT IS ODD. numColumns gives the last
  // card a row to itself and flex: 1 makes it fill that row, so a list
  // ending on an odd number renders one product at double width.
  const grid = React.useMemo(() => {
    const items: (FeedProduct | null)[] = [...feed.products];
    if (items.length % COLUMNS !== 0) items.push(null);
    return items;
  }, [feed.products]);

  const header = (
    <>
      <BrowseHeader
        label={title}
        total={feed.total}
        search={controls.search ?? ""}
        onSearch={feed.setSearch}
      />
      {/* THE BAR SURVIVES AN EMPTY RESULT. A filter that returns nothing
          and then removes the controls that caused it strands the
          reader with no way back except the system back button. */}
      {feed.suppliers.length > 0 || narrowed ? (
        <BrowseFilterBar
          suppliers={feed.suppliers}
          activeSupplier={controls.supplier}
          sort={(controls.sort ?? "relevance") as any}
          sortOptions={SEE_ALL_SORTS as any}
          onToggleSupplier={feed.toggleSupplier}
          onSort={feed.setSort}
        />
      ) : null}
    </>
  );

  if (feed.isError) {
    return (
      <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
        {header}
        <ErrorState message="Could not load this list." onRetry={feed.refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      {header}

      {feed.isLoading ? (
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      ) : (
        <FlatList
          data={grid}
          numColumns={COLUMNS}
          keyExtractor={(product, index) => product?.id ?? `spacer-${index}`}
          columnWrapperStyle={styles.row}
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
          refreshControl={
            <RefreshControl
              refreshing={feed.isRefetching}
              onRefresh={feed.refetch}
              tintColor={theme.colors.primary}
            />
          }
          renderItem={({ item }) =>
            item === null ? (
              <View style={styles.cell} />
            ) : (
              <View style={styles.cell}>
                <ProductTile
                  product={item}
                  width="100%"
                  onPress={() =>
                    router.push(
                      productDetailHref(
                        item.supplierId,
                        item.id,
                        item.name,
                        item.supplierName
                      ) as any
                    )
                  }
                />
              </View>
            )
          }
          onEndReachedThreshold={0.5}
          onEndReached={() => {
            if (feed.hasNextPage && !feed.isFetchingNextPage) feed.fetchNextPage();
          }}
          ListFooterComponent={
            feed.isFetchingNextPage ? (
              <View style={styles.footer}>
                <ActivityIndicator color={theme.colors.primary} />
              </View>
            ) : null
          }
          ListEmptyComponent={
            <View style={styles.centre}>
              {/* TWO DIFFERENT EMPTIES, because they are two different
                  facts and one of them is the reader's own doing.
                  Telling somebody who has just typed a word that their
                  whole reorder list is empty is both wrong and
                  discouraging. */}
              <Text style={[styles.emptyTitle, { color: theme.colors.onSurface }]}>
                {narrowed ? "Nothing matches" : emptyTitle}
              </Text>
              <Text style={[styles.emptyBody, { color: theme.colors.onSurfaceVariant }]}>
                {narrowed
                  ? "Try a different search, or clear the filters to see the whole list."
                  : emptyBody}
              </Text>
            </View>
          }
        />
      )}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, gap: spacing.md },
  row: { gap: spacing.md },
  cell: { flex: 1 },
  footer: { paddingVertical: spacing.lg },
  centre: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
    paddingTop: spacing.xxl,
    paddingHorizontal: spacing.lg,
  },
  emptyTitle: { ...typography.h2, textAlign: "center" },
  emptyBody: { ...typography.body, textAlign: "center" },
});
