import React from "react";
import { FlatList, Pressable, StyleSheet, Text } from "react-native";
import { useTheme } from "react-native-paper";
import { CategoryIcon } from "@/components/categories";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { FeedCategory } from "../../types";

/**
 * ICONS COME FROM components/categories, NOT FROM A MAP HERE.
 *
 * This file used to own a deliberately small, curated set of six
 * glyphs, on the reasoning that a category row is scanned rather than
 * read and a dozen similar shapes would slow that down. That was right
 * when it was written and stopped being right when the taxonomy grew:
 * with seventeen categories, ELEVEN of them fell back to the same
 * parcel, so the row was six icons and eleven identical blanks --
 * slower to scan than distinct glyphs, not faster.
 *
 * CategoryIcon now holds one considered icon per category AND resolves
 * the server-supplied name, so the forward-compatibility rule this
 * comment used to defend still holds -- the server names an icon, the
 * app prefers it, and anything unrecognised degrades to the app's own
 * choice rather than to a hole. One map, one place.
 */
export function CategoryChipRow({
  categories,
  onSelect,
}: {
  categories: FeedCategory[];
  onSelect: (category: FeedCategory) => void;
}) {
  const theme = useTheme();

  return (
    <FlatList
      horizontal
      data={categories}
      keyExtractor={(category) => category.value}
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.row}
      renderItem={({ item }) => {

        return (
          <Pressable
            onPress={() => onSelect(item)}
            style={({ pressed }) => [
              styles.chip,
              {
                backgroundColor: theme.colors.surface,
                borderColor: theme.colors.outlineVariant,
                opacity: pressed ? 0.7 : 1,
              },
            ]}
            accessibilityRole="button"
            accessibilityLabel={item.label}
          >
            <CategoryIcon
              category={item.value}
              name={item.icon}
              size={16}
              color={theme.colors.onSurfaceVariant}
              strokeWidth={2.2}
            />
            <Text style={[styles.label, { color: theme.colors.onSurface }]}>{item.label}</Text>
          </Pressable>
        );
      }}
    />
  );
}

const styles = StyleSheet.create({
  row: { paddingHorizontal: spacing.md, gap: spacing.sm },
  chip: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.pill,
    borderWidth: 1,
    minHeight: 40,
  },
  label: { ...typography.bodySmall, fontWeight: "700" },
});
