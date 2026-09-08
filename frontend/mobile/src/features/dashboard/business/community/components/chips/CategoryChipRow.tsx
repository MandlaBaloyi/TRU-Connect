import React from "react";
import { FlatList, Pressable, StyleSheet, Text } from "react-native";
import { useTheme } from "react-native-paper";
import {
  Beef,
  Carrot,
  Croissant,
  CupSoda,
  Package,
  SprayCan,
  type LucideIcon,
} from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { FeedCategory } from "../../types";

/**
 * ICONS RESOLVED BY NAME, sent by the server.
 *
 * The alternative -- the app deciding which icon each category gets --
 * means a new product category cannot appear in this row until every
 * installed build has been updated. The server names an icon, the app
 * looks it up here, and anything it does not recognise falls back
 * rather than crashing. Same forward-compatibility rule as unknown
 * section types (see types.ts).
 *
 * DELIBERATELY A SMALL, CURATED SET rather than every icon in the
 * library. A category row is scanned, not read, and a dozen visually
 * similar glyphs would slow that down; the fallback is honest and
 * unremarkable, which is exactly what an unmapped category deserves.
 */
const ICONS: Record<string, LucideIcon> = {
  CupSoda,
  Beef,
  Carrot,
  Croissant,
  SprayCan,
  Package,
};

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
        const Icon = (item.icon && ICONS[item.icon]) || Package;
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
            <Icon size={16} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />
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
