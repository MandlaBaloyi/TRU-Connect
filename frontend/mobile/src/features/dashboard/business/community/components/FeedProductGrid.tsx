import React from "react";
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { ErrorState } from "@/components/feedback/ErrorState";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { productDetailHref } from "../../routes";
import { ProductTile } from "./cards/ProductTile";
import type { FeedProduct } from "../types";

const COLUMNS = 3;

/**
 * The 3-wide grid every "see all" product screen uses.
 *
 * THREE ACROSS, because that is the shape of every stock-browsing app a
 * shopkeeper already uses, and because a rail's job and a screen's job
 * are different: a rail is a preview you glance along, a screen is a
 * catalogue you search with your eyes. Two columns wastes the width;
 * four makes the price unreadable on a cheap handset.
 *
 * THE SAME ProductTile THE RAILS USE, at a width the grid computes.
 * A second card component would have drifted -- the tile carries the
 * supplier's name, the verification tick, the saving pill, the
 * out-of-stock scrim and the "Bought by N businesses" line, and every
 * one of those would eventually have been fixed in one place only.
 *
 * ONE SCREEN SHAPE FOR THREE DESTINATIONS. Buy it again, Moving fast
 * and Stock for your shop differ only in their title and their query;
 * writing three screens would have been three chances to disagree
 * about empty states, paging and pull-to-refresh.
 */
export function FeedProductGrid({
  products,
  total,
  emptyTitle,
  emptyBody,
  isLoading,
  isError,
  refetch,
  isRefetching,
  onEndReached,
  isFetchingNextPage,
}: {
  products: FeedProduct[];
  total: number;
  emptyTitle: string;
  emptyBody: string;
  isLoading: boolean;
  isError: boolean;
  refetch: () => void;
  isRefetching: boolean;
  onEndReached: () => void;
  isFetchingNextPage: boolean;
}) {
  const router = useRouter();
  const theme = useTheme();

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
        <ErrorState
          message="Couldn't load this list. Check your connection and try again."
          onRetry={refetch}
        />
      </ScreenContainer>
    );
  }

  if (products.length === 0) {
    // A DESIGNED EMPTY, not a blank screen. Every one of these lists is
    // legitimately empty for a new shop, and arriving at nothing with no
    // explanation reads as broken rather than as early.
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <Text style={[styles.emptyTitle, { color: theme.colors.onSurface }]}>
            {emptyTitle}
          </Text>
          <Text style={[styles.emptyBody, { color: theme.colors.onSurfaceVariant }]}>
            {emptyBody}
          </Text>
        </View>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader>
      <FlatList
        data={products}
        numColumns={COLUMNS}
        keyExtractor={(product) => product.id}
        columnWrapperStyle={styles.row}
        contentContainerStyle={styles.content}
        ListHeaderComponent={
          <Text style={[styles.count, { color: theme.colors.onSurfaceVariant }]}>
            {total} {total === 1 ? "product" : "products"}
          </Text>
        }
        renderItem={({ item }) => (
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
        )}
        onEndReached={onEndReached}
        // HALF A SCREEN AHEAD. Fetching at the very end makes a cheap
        // handset show a spinner every time; fetching too early pays
        // for pages nobody reaches on prepaid data.
        onEndReachedThreshold={0.5}
        ListFooterComponent={
          isFetchingNextPage ? (
            <ActivityIndicator style={styles.footer} color={theme.colors.primary} />
          ) : null
        }
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={refetch}
            tintColor={theme.colors.primary}
          />
        }
        showsVerticalScrollIndicator={false}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, gap: spacing.lg },
  row: { gap: spacing.sm },
  // flex:1 on the cell rather than a fixed width, so the tile fits
  // whatever the device gives us instead of assuming a screen size.
  cell: { flex: 1 / COLUMNS },
  centre: { flex: 1, alignItems: "center", justifyContent: "center", padding: spacing.xl, gap: spacing.sm },
  emptyTitle: { ...typography.h2, textAlign: "center" },
  emptyBody: { ...typography.bodySmall, textAlign: "center" },
  count: { ...typography.caption },
  footer: { paddingVertical: spacing.lg },
});
