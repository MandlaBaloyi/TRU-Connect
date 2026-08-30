import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { ChevronDown, SlidersHorizontal } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  itemCount: number;
  /** True once a real (non-null) category filter is active -- shown
   *  as a filled pill rather than an outline one, same "selected looks
   *  different from unselected" convention ProductStatusFilterBar.tsx
   *  already uses elsewhere in this app. */
  filterActive: boolean;
  onPressSort: () => void;
  onPressFilter: () => void;
}

/** The row shown above the catalogue grid -- "X items", then Sort and
 *  Filter as pill buttons, matching the reference screenshots'
 *  layout. Deliberately a standalone component, not inlined into
 *  SupplierCatalogScreen.tsx -- this exact row gets rendered TWICE
 *  (once inline, once as the pinned sticky copy once scrolled past),
 *  and a shared component is what keeps those two renders from ever
 *  silently drifting apart. */
export function CatalogControlsRow({ itemCount, filterActive, onPressSort, onPressFilter }: Props) {
  const theme = useTheme();

  return (
    <View style={styles.row}>
      <Text style={[styles.count, { color: theme.colors.onSurfaceVariant }]}>
        {itemCount} item{itemCount === 1 ? "" : "s"}
      </Text>
      <View style={styles.buttons}>
        <Pressable
          onPress={onPressSort}
          style={[styles.pill, { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface }]}
          accessibilityRole="button"
          accessibilityLabel="Sort"
        >
          <Text style={[styles.pillLabel, { color: theme.colors.onSurface }]}>Sort</Text>
          <ChevronDown size={16} color={theme.colors.onSurface} strokeWidth={2} />
        </Pressable>
        <Pressable
          onPress={onPressFilter}
          style={[
            styles.pill,
            { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
            filterActive && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
          ]}
          accessibilityRole="button"
          accessibilityLabel="Filter"
          accessibilityState={{ selected: filterActive }}
        >
          <Text style={[styles.pillLabel, { color: filterActive ? theme.colors.onPrimary : theme.colors.onSurface }]}>
            Filter
          </Text>
          <SlidersHorizontal size={15} color={filterActive ? theme.colors.onPrimary : theme.colors.onSurface} strokeWidth={2} />
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingVertical: spacing.sm },
  count: { ...typography.bodySmall },
  buttons: { flexDirection: "row", gap: spacing.sm },
  pill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: radius.pill,
    minHeight: 36,
    borderWidth: 1,
  },
  pillLabel: { ...typography.bodySmall, fontWeight: "600" },
});
