import React from "react";
import { FlatList, RefreshControl, StyleSheet, View } from "react-native";
import { useTheme } from "react-native-paper";

import { ErrorState } from "@/components/feedback/ErrorState";
import { radius, spacing } from "@/theme/spacing";

import { FeedSectionView } from "./FeedSectionView";
import { useCommunityFeed } from "../../hooks/useCommunityFeed";

/**
 * The "For You" feed: a vertical list of horizontal shelves.
 *
 * A FlatList OF SECTIONS, not a ScrollView. Same reasoning as inside
 * each Rail, one level up: a ScrollView would mount every shelf on the
 * screen at once, and each shelf mounts its own images. On a cheap
 * Android handset over prepaid data that means paying for the whole
 * feed before the user has scrolled past the first rail.
 *
 * PULL TO REFRESH, because the two things this screen is most useful
 * for -- what did I buy last time, and who is around now -- both go
 * stale within a day.
 */
export function CommunityFeed() {
  const theme = useTheme();
  const { sections, isLoading, isError, refetch, isRefetching } = useCommunityFeed();

  if (isLoading) return <FeedSkeleton />;

  if (isError) {
    return (
      <ErrorState
        message="Couldn't load your feed. Check your connection and try again."
        onRetry={refetch}
      />
    );
  }

  return (
    <FlatList
      data={sections}
      keyExtractor={(section) => section.id}
      renderItem={({ item }) => <FeedSectionView section={item} />}
      ItemSeparatorComponent={() => <View style={styles.gap} />}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={isRefetching}
          onRefresh={refetch}
          tintColor={theme.colors.primary}
        />
      }
      initialNumToRender={3}
      maxToRenderPerBatch={2}
      windowSize={5}
      removeClippedSubviews
    />
  );
}

/**
 * A SHAPED skeleton, not a spinner.
 *
 * The feed's first paint decides whether this screen feels fast, and a
 * centred spinner tells a user nothing about what is coming. Grey
 * blocks in the real proportions of the first two rails mean the
 * layout does not jump when content lands -- and the loading state is
 * something that was actually designed rather than whatever a
 * component library shipped with.
 */
function FeedSkeleton() {
  const theme = useTheme();
  const block = { backgroundColor: theme.colors.surfaceVariant };

  return (
    <View style={styles.skeleton} pointerEvents="none">
      <View style={styles.skeletonChips}>
        {[0, 1, 2, 3].map((key) => (
          <View key={key} style={[styles.skeletonChip, block]} />
        ))}
      </View>

      {[0, 1].map((rail) => (
        <View key={rail} style={styles.skeletonRail}>
          <View style={[styles.skeletonTitle, block]} />
          <View style={styles.skeletonRow}>
            {[0, 1, 2].map((card) => (
              <View key={card} style={[styles.skeletonCard, block]} />
            ))}
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.md, paddingBottom: spacing.xxl },
  gap: { height: spacing.lg },

  skeleton: { paddingVertical: spacing.md, gap: spacing.lg },
  skeletonChips: { flexDirection: "row", gap: spacing.sm, paddingHorizontal: spacing.md },
  skeletonChip: { width: 92, height: 40, borderRadius: radius.pill },
  skeletonRail: { gap: spacing.sm },
  skeletonTitle: { width: 160, height: 18, borderRadius: radius.sm, marginHorizontal: spacing.md },
  skeletonRow: { flexDirection: "row", gap: spacing.sm, paddingHorizontal: spacing.md },
  skeletonCard: { width: 148, height: 168, borderRadius: radius.md },
});
