import React from "react";
import { FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { ChevronRight } from "lucide-react-native";

import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * A horizontal shelf: title, optional "see all", and a row that
 * scrolls sideways. Every section on the Community feed that shows
 * more than one thing is one of these.
 *
 * ONE IMPLEMENTATION, USED BY EVERY RAIL, including the supplier
 * profile's own showcase strips once those are moved onto it. Rails
 * are the single most repeated shape on this screen, and the fastest
 * way to make a feed look homemade is three shelves with slightly
 * different header spacing and slightly different card gaps.
 *
 * FlatList RATHER THAN A ScrollView OF CHILDREN, and this one matters
 * more here than in most apps. These rails are image-heavy and the
 * phones this is built for are cheap Android handsets on prepaid data.
 * A ScrollView mounts and downloads every card in the row immediately,
 * including the six off-screen ones nobody scrolls to. FlatList
 * windows them, so an unscrolled rail costs roughly what is visible.
 *
 * THE TITLE ROW IS ONLY PRESSABLE WHEN THERE IS SOMEWHERE TO GO. A
 * chevron that does nothing is worse than no chevron -- it reads as
 * broken rather than as decoration.
 */
export function Rail<T>({
  title,
  subtitle,
  data,
  keyExtractor,
  renderItem,
  onSeeAll,
  itemGap = spacing.sm,
}: {
  title: string;
  subtitle?: string | null;
  data: T[];
  keyExtractor: (item: T) => string;
  /** THE INDEX IS PASSED BECAUSE IMPRESSIONS NEED IT. A tap is only
   *  worth recording if it can name WHERE in the rail it happened --
   *  the whole reason tier_rules' distance band can be argued with is
   *  comparing position 0 against position 1. Callers that do not care
   *  simply ignore it. */
  renderItem: (item: T, index: number) => React.ReactElement;
  onSeeAll?: (() => void) | null;
  itemGap?: number;
}) {
  const theme = useTheme();

  const header = (
    <View style={styles.headerText}>
      <Text style={[styles.title, { color: theme.colors.onSurface }]} numberOfLines={1}>
        {title}
      </Text>
      {subtitle ? (
        <Text style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
          {subtitle}
        </Text>
      ) : null}
    </View>
  );

  return (
    <View style={styles.wrap}>
      {onSeeAll ? (
        <Pressable
          onPress={onSeeAll}
          style={styles.headerRow}
          accessibilityRole="button"
          accessibilityLabel={`${title}, see all`}
        >
          {header}
          {/* BIGGER AND HEAVIER THAN A LIST CHEVRON, on purpose. This
              is not decoration on a row -- it is the ONLY way to reach
              the other ninety products in a rail that shows twelve, and
              at 20px/2.2 it read as an ornament next to the heading.
              A shopkeeper who restocks a hundred lines cannot scroll
              sideways to find them; they have to know there is a door
              here. */}
          <ChevronRight
            size={24}
            color={theme.colors.onSurface}
            strokeWidth={3}
          />
        </Pressable>
      ) : (
        <View style={styles.headerRow}>{header}</View>
      )}

      <FlatList
        horizontal
        data={data}
        keyExtractor={keyExtractor}
        renderItem={({ item, index }) => renderItem(item, index)}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={[styles.row, { gap: itemGap }]}
        // Windowing kept tight on purpose -- see the note above on
        // data cost. Two screens' worth of cards is plenty of runway
        // for a horizontal scroll and stops the rail pre-fetching
        // images for cards nobody reaches.
        initialNumToRender={3}
        maxToRenderPerBatch={3}
        windowSize={3}
        removeClippedSubviews
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.sm },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  headerText: { flex: 1, gap: 1 },
  title: { ...typography.body, fontWeight: "800", fontSize: 17 },
  subtitle: { ...typography.bodySmall, fontSize: 12 },
  row: { paddingHorizontal: spacing.md },
});
