import React from "react";
import { ActivityIndicator, FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { ChevronRight } from "lucide-react-native";

import { EntityAvatar } from "@/components/ui/EntityAvatar";
import { SupplierName } from "@/components/ui/SupplierName";
import { ErrorState } from "@/components/feedback/ErrorState";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
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
  suppliers,
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
  suppliers: FeedSupplier[];
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

  if (suppliers.length === 0) {
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
        data={suppliers}
        keyExtractor={(supplier) => supplier.id}
        contentContainerStyle={styles.content}
        ItemSeparatorComponent={() => (
          <View style={[styles.separator, { backgroundColor: theme.colors.outlineVariant }]} />
        )}
        ListHeaderComponent={
          <Text style={[styles.count, { color: theme.colors.onSurfaceVariant }]}>
            {total} {total === 1 ? "supplier" : "suppliers"}
          </Text>
        }
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
        onEndReached={onEndReached}
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
