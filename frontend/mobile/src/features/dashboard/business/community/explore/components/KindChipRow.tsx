import React from "react";
import { FlatList, Pressable, StyleSheet, Text } from "react-native";
import { useTheme } from "react-native-paper";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { iconForKind, labelForKind } from "../services/exploreService";

/**
 * Which SORT of supplier to browse.
 *
 * THE CHIPS COME FROM THE SERVER, NOT FROM AN ENUM IN THIS APP, and
 * that is the whole design. The server lists only kinds that actually
 * have a visible supplier with stock behind them, so this row can never
 * offer a filter that returns nothing. An empty result from a chip the
 * app drew itself reads as broken; a chip that is simply not there
 * reads as "not yet", which is the truth.
 *
 * NO "ALL" CHIP. It is tempting and it is wrong here: the kinds are not
 * facets of one list, they are four different questions -- "show me
 * wholesalers" and "show me manufacturers" are separate intents, and a
 * mixed list answers neither. The backend agrees; it defaults to
 * WHOLESALER rather than to everything.
 *
 * SELECTION IS FILLED, NOT OUTLINED. A row where the selected chip is
 * only a slightly different border is one people tap twice because
 * they cannot tell whether the first tap registered.
 */
export function KindChipRow({
  kinds,
  selected,
  onSelect,
}: {
  kinds: string[];
  selected: string | undefined;
  onSelect: (kind: string) => void;
}) {
  const theme = useTheme();

  // The server defaults to WHOLESALER when nothing is asked for, so
  // that is what "nothing selected" actually means on screen. Showing
  // no chip as active while a filtered list sits underneath would be
  // the app disagreeing with itself.
  const active = selected ?? (kinds.includes("WHOLESALER") ? "WHOLESALER" : kinds[0]);

  return (
    <FlatList
      horizontal
      // flexGrow: 0 OR THE ROW EATS THE SCREEN. A horizontal FlatList is
      // still a flex child of a column, so without this it expands to
      // fill whatever height is left and centres its chips in the
      // middle of it -- which is why this screen had a hundred points
      // of blank space above the chips and another eighty below. The
      // contentContainer's alignItems fixed the CHIPS; this fixes the
      // LIST.
      style={styles.list}
      data={kinds}
      keyExtractor={(kind) => kind}
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.row}
      renderItem={({ item }) => {
        const isActive = item === active;
        return (
          <Pressable
            onPress={() => onSelect(item)}
            style={({ pressed }) => [
              styles.chip,
              {
                backgroundColor: isActive ? theme.colors.primary : theme.colors.surface,
                borderColor: isActive ? theme.colors.primary : theme.colors.outlineVariant,
                opacity: pressed ? 0.7 : 1,
              },
            ]}
            accessibilityRole="button"
            accessibilityState={{ selected: isActive }}
            accessibilityLabel={labelForKind(item)}
          >
            {(() => {
              const Icon = iconForKind(item);
              return (
                <Icon
                  size={16}
                  strokeWidth={1.8}
                  color={isActive ? theme.colors.onPrimary : theme.colors.onSurfaceVariant}
                />
              );
            })()}
            <Text
              style={[
                styles.label,
                { color: isActive ? theme.colors.onPrimary : theme.colors.onSurface },
              ]}
            >
              {labelForKind(item)}
            </Text>
          </Pressable>
        );
      }}
    />
  );
}

const styles = StyleSheet.create({
  list: { flexGrow: 0 },
  // alignItems: "center" IS THE BUG FIX, not decoration. A horizontal
  // FlatList's content container defaults to align-items: stretch, so
  // every chip grew to the full height the list was given -- which on
  // this screen is whatever is left under the header. The chips
  // rendered as enormous vertical pills. Pinning the cross-axis here
  // makes each chip its own content height regardless of what the
  // parent hands the list.
  row: {
    alignItems: "center",
    paddingHorizontal: spacing.md,
    gap: spacing.sm,
    paddingVertical: spacing.sm,
  },
  // THE SAME SHAPE AS CategoryChipRow's chip, deliberately: these two
  // rows do the same job on two screens and should not be two
  // different controls.
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
