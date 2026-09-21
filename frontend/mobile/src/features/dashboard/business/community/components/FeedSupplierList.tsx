import React from "react";
import { ActivityIndicator, FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { ChevronRight } from "lucide-react-native";

import { EntityAvatar } from "@/components/ui/EntityAvatar";
import { SupplierName } from "@/components/ui/SupplierName";
import { ErrorState } from "@/components/feedback/ErrorState";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { BrowseFilterBar } from "@/features/dashboard/business/browse/components/BrowseFilterBar";
import { BrowseHeader } from "@/features/dashboard/business/browse/components/BrowseHeader";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { supplierProfileHref } from "../../routes";
import type { FeedSupplier } from "../types";

/**
 * A VERTICAL LIST of suppliers: avatar, name, tick, distance, chevron.
 *
 * A LIST AND NOT A GRID, deliberately, and the distinction is about
 * what the reader is doing. A grid is for comparing GOODS -- price and
 * picture, scanned in parallel. A list is for choosing between
 * ENTITIES, where each row carries a different kind of fact (how far,
 * how verified, how known) and you read them one at a time. Suppliers
 * are entities.
 *
 * THE DISTANCE IS THE POINT ON THIS SCREEN, so it sits where the eye
 * lands after the name rather than buried in a meta line. It is also
 * why nothing here reorders: this list is sorted by the number it
 * prints, and any other order would be a contradiction the reader is
 * holding (V2_17 Q5).
 */
export function FeedSupplierList({
  title,
  feed,
  emptyTitle,
  emptyBody,
}: {
  title: string;
  /** The whole useFeedSuppliers result. Passed wholesale rather than as
   *  a dozen props: the hook owns the filters precisely so the screen
   *  and the query cannot disagree. */
  feed: {
    suppliers: FeedSupplier[];
    total: number | null;
    kinds: { id: string; name: string; count: number }[];
    controls: { search?: string; kind?: string | null };
    setSearch: (value: string) => void;
    toggleKind: (id: string) => void;
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

  const { controls, suppliers } = feed;
  const narrowed = Boolean(controls.search || controls.kind);

  const header = (
    <>
      <BrowseHeader
        label={title}
        total={feed.total}
        search={controls.search ?? ""}
        onSearch={feed.setSearch}
        noun={{ one: "supplier", many: "suppliers" }}
      />
      {/* KIND CHIPS AND NOTHING ELSE. No sort: collect-near-you prints
          the distance it is ordered by, so a reorder would contradict
          the number on its own cards (V2_17 Q5). Narrowing is safe --
          filtering to wholesalers leaves the survivors in distance
          order and the heading stays true.

          NO "MY SUPPLIERS" EITHER: one of these lists is suppliers this
          shop has never bought from, so the toggle would empty it. */}
      {feed.kinds.length > 0 || narrowed ? (
        <BrowseFilterBar
          kinds={feed.kinds}
          suppliers={[]}
          activeKind={controls.kind}
          sort={"name" as any}
          sortOptions={[] as any}
          onToggleKind={feed.toggleKind}
          onToggleSupplier={() => {}}
          onSort={() => {}}
          hideSort
        />
      ) : null}
    </>
  );

  if (feed.isError) {
    return (
      <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
        {header}
        <ErrorState message="Could not load suppliers." onRetry={feed.refetch} />
      </ScreenContainer>
    );
  }

  if (feed.isLoading) {
    return (
      <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
        {header}
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (suppliers.length === 0) {
    return (
      <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
        {header}
        <View style={styles.centre}>
          {/* TWO DIFFERENT EMPTIES -- one is the market, the other is
              the reader's own filter, and telling somebody who just
              typed a word that nobody is near them is wrong. */}
          <Text style={[styles.emptyTitle, { color: theme.colors.onSurface }]}>
            {narrowed ? "Nothing matches" : emptyTitle}
          </Text>
          <Text style={[styles.emptyBody, { color: theme.colors.onSurfaceVariant }]}>
            {narrowed
              ? "Try a different search, or clear the filters to see everyone."
              : emptyBody}
          </Text>
        </View>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      {header}
      <FlatList
        data={suppliers}
        keyExtractor={(supplier) => supplier.id}
        contentContainerStyle={styles.content}
        ItemSeparatorComponent={() => (
          <View style={[styles.separator, { backgroundColor: theme.colors.outlineVariant }]} />
        )}
        renderItem={({ item }) => (
          <Pressable
            onPress={() => router.push(supplierProfileHref(item.id, item.businessName) as any)}
            style={({ pressed }) => [styles.row, { opacity: pressed ? 0.85 : 1 }]}
            accessibilityRole="button"
            accessibilityLabel={[
              item.businessName,
              item.distanceKm != null ? `${item.distanceKm} kilometres away` : null,
              item.location,
            ]
              .filter(Boolean)
              .join(", ")}
          >
            <EntityAvatar name={item.businessName} photoUrl={item.businessImageUrl} size={44} />
            <View style={styles.rowText}>
              <SupplierName
                name={item.businessName}
                verificationStatus={item.verificationStatus}
                style={[styles.name, { color: theme.colors.onSurface }]}
              />
              <Text style={[styles.meta, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
                {[
                  item.distanceKm != null ? `${item.distanceKm} km away` : null,
                  item.location,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </Text>
            </View>
            <ChevronRight size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
          </Pressable>
        )}
        onEndReached={() => {
          if (feed.hasNextPage && !feed.isFetchingNextPage) feed.fetchNextPage();
        }}
        onEndReachedThreshold={0.5}
        ListFooterComponent={
          feed.isFetchingNextPage ? (
            <ActivityIndicator style={styles.footer} color={theme.colors.primary} />
          ) : null
        }
        refreshControl={
          <RefreshControl
            refreshing={feed.isRefetching}
            onRefresh={feed.refetch}
            tintColor={theme.colors.primary}
          />
        }
        showsVerticalScrollIndicator={false}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.md },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
  },
  rowText: { flex: 1, gap: 2 },
  name: { ...typography.body, fontWeight: "700" },
  meta: { ...typography.caption },
  separator: { height: StyleSheet.hairlineWidth, marginLeft: spacing.md + 44 + spacing.md },
  centre: { flex: 1, alignItems: "center", justifyContent: "center", padding: spacing.xl, gap: spacing.sm },
  emptyTitle: { ...typography.h2, textAlign: "center" },
  emptyBody: { ...typography.bodySmall, textAlign: "center" },
  count: { ...typography.caption, paddingHorizontal: spacing.md, paddingBottom: spacing.sm },
  footer: { paddingVertical: spacing.lg },
});
