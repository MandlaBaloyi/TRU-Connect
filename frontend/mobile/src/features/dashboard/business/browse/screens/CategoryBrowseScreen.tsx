import React from "react";
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { CategoryIcon } from "@/components/categories";
import { ErrorState } from "@/components/feedback/ErrorState";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { categoryLabel } from "@/constants/productCategories";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { BrowseFilterBar } from "../components/BrowseFilterBar";
import { BrowseHeader } from "../components/BrowseHeader";
import { BrowseProductCard } from "../components/BrowseProductCard";
import { useCategoryBrowse } from "../hooks/useCategoryBrowse";

/**
 * Where a category chip finally lands.
 *
 * IT USED TO GO TO SUPPLIER SEARCH. Tapping "Drinks" found SHOPS, not
 * drinks -- and for a business that has just installed the app, the
 * chips are the ONLY section of the Community tab that works at all.
 * So the first thing a new user did was the thing that worked least.
 *
 * AND THEN IT WAS A DEAD END AT TWENTY-FOUR. The screen read one page
 * and never asked for another: Food & Grocery held 253 offers and 229
 * of them could not be reached by any gesture. That is the bug this
 * version fixes, and it mattered more than the layout it arrived with.
 *
 * NARROWING IS THE DESIGN, NOT DENSITY. Seventeen flat categories mean
 * "Food & Grocery" is one bucket holding flour, oil, sugar and rice,
 * and nobody browses a thousand products -- a shopkeeper opens this
 * wanting cooking oil. Halving the card height takes a screenful from
 * five products to eight, which against a thousand is nothing. Search,
 * brand and "my suppliers" are what make the screen usable; the denser
 * cards are a courtesy on top.
 *
 * THE CONTROLS ARE PINNED, THE LIST SCROLLS. Filters that scroll away
 * are filters you have to scroll back for, and the moment a reader
 * needs them is the moment they have scrolled far enough to be lost.
 *
 * STOCK ACROSS EVERY VISIBLE SUPPLIER, which is only possible because
 * browsing was opened at the platform level (V2_00 2.3): the connection
 * is the supplier's optional gate on ORDERING, never on seeing. "My
 * suppliers" is the shop choosing to see less, which is a different
 * thing entirely.
 */
export default function CategoryBrowseScreen() {
  const { category } = useLocalSearchParams<{ category?: string }>();
  const theme = useTheme();
  const router = useRouter();

  const label = category ? categoryLabel(category) : "Browse";
  const browse = useCategoryBrowse(category);
  const { filters } = browse;

  const filtered = Boolean(
    filters.search || filters.kind || filters.supplier || filters.mineOnly
  );

  // A TRAILING SPACER WHEN THE COUNT IS ODD. numColumns={2} gives the
  // last card a row to itself, and flex: 1 makes it fill that row --
  // so a 77-product category ends with one product rendered at double
  // width, looking like a feature nobody asked for. An invisible
  // partner keeps the grid a grid.
  const grid = React.useMemo(() => {
    const items: (typeof browse.products[number] | null)[] = [...browse.products];
    if (items.length % 2 === 1) items.push(null);
    return items;
  }, [browse.products]);

  const header = (
    <>
      <BrowseHeader
        category={category}
        label={label}
        total={browse.total}
        search={filters.search ?? ""}
        onSearch={browse.setSearch}
      />
      {/* THE BAR SURVIVES AN EMPTY RESULT, deliberately. A filter that
          returns nothing and then removes the controls that caused it
          strands the reader on a dead screen with no way back except
          the back button -- which loses the category too. */}
      <BrowseFilterBar
        kinds={browse.kinds}
        suppliers={browse.suppliers}
        activeKind={filters.kind}
        activeSupplier={filters.supplier}
        mineOnly={filters.mineOnly}
        sort={filters.sort ?? "name"}
        onToggleKind={browse.toggleKind}
        onToggleSupplier={browse.toggleSupplier}
        onToggleMine={browse.toggleMine}
        onSort={browse.setSort}
      />
    </>
  );

  if (browse.isError) {
    return (
      <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
        {header}
        <ErrorState message="Could not load this category." onRetry={browse.refetch} />
      </ScreenContainer>
    );
  }

  return (
    // edges WITHOUT "top", AND NOT hasNativeHeader -- the exact
    // configuration every AppHeader screen in this app uses, and the
    // difference is not cosmetic.
    //
    // hasNativeHeader LOOKS RIGHT AND IS NOT. It excludes the top
    // safe-area edge, which is wanted, but it ALSO adds
    // paddingTop: spacing.md to its inner View -- breathing room meant
    // for a screen sitting under a native header. AppHeader paints the
    // status-bar strip itself, so that padding inserted sixteen points
    // of CONTAINER background above it: a band of one colour behind the
    // clock and the battery, then the header's own colour underneath.
    // Two bars where there should be one.
    //
    // This is why the header had to be AppHeader rather than a bespoke
    // row. A hand-rolled bar can be made to look right on one device
    // and gets the status-bar region wrong on the next; AppHeader
    // already owns that region, measures it from StatusBar.currentHeight
    // on Android, and carries the comment explaining why.
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      {header}

      {browse.isLoading ? (
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      ) : (
        <FlatList
          data={grid}
          keyExtractor={(product, index) => product?.id ?? `spacer-${index}`}
          numColumns={2}
          columnWrapperStyle={styles.row}
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
          renderItem={({ item }) =>
            item === null ? (
              <View style={styles.spacer} />
            ) : (
            <BrowseProductCard
              product={item}
              // Straight to the product on ITS supplier's shopfront --
              // the screen that already knows how to show one product,
              // rather than a second product detail built for this list.
              onPress={() =>
                router.push(
                  `/business/my-suppliers/${item.supplierId}/products/${item.id}` as any
                )
              }
            />
            )
          }
          onEndReachedThreshold={0.5}
          onEndReached={() => {
            if (browse.hasNextPage && !browse.isFetchingNextPage) browse.fetchNextPage();
          }}
          ListFooterComponent={
            browse.isFetchingNextPage ? (
              <View style={styles.footer}>
                <ActivityIndicator color={theme.colors.primary} />
              </View>
            ) : null
          }
          ListEmptyComponent={
            <View style={styles.centre}>
              <CategoryIcon
                category={category ?? "OTHER"}
                size={40}
                color={theme.colors.onSurfaceVariant}
              />
              {/* TWO DIFFERENT EMPTIES, because they are two different
                  facts and one of them is the reader's own doing. "No
                  food & grocery yet" told somebody who had just typed a
                  word that the whole category was empty, which is both
                  wrong and discouraging. */}
              <Text style={[styles.emptyTitle, { color: theme.colors.onSurface }]}>
                {filtered ? "Nothing matches" : `No ${label.toLowerCase()} yet`}
              </Text>
              <Text style={[styles.emptyBody, { color: theme.colors.onSurfaceVariant }]}>
                {filtered
                  ? "Try a different search, or clear the filters to see everything in this category."
                  : "Nobody is selling in this category right now. Try another one, or invite a supplier you already buy from."}
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
  footer: { paddingVertical: spacing.lg },
  spacer: { flex: 1 },
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
