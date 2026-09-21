import React from "react";
import { FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Compass } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { iconForKind, labelForKind } from "../../explore/services/exploreService";

/**
 * The last thing in the feed: the ways into Explore.
 *
 * A SIDEWAYS CHIP ROW, THE SAME SHAPE AS THE CATEGORY CHIPS AT THE TOP
 * OF THIS FEED. The first version was a vertical menu, argued for on
 * the grounds that four doors are a finite set and a horizontal scroll
 * would hide the fourth. That reasoning was about the CHIPS and missed
 * the SCREEN: every other section here scrolls sideways, so a column
 * reads as a different kind of object -- a settings list that wandered
 * into a feed -- and the eye stops at it instead of passing through.
 *
 * Matching the category row also puts the two ways of narrowing the
 * market into one control: by WHAT you want at the top, by WHO sells it
 * at the bottom, the same shape at both ends.
 *
 * EACH CHIP IS A DOORWAY, NOT A FILTER, and that is the one way this
 * differs from the category chips and from Explore's own KindChipRow.
 * Nothing here is ever "selected" -- tapping leaves the screen. So
 * there is no active state to draw, and drawing one would promise a
 * filter this row does not apply.
 *
 * EVERY CHIP CARRIES ITS ICON, the same treatment the categories get.
 * Four pills of plain text are four words to read; a warehouse, a
 * truck, a factory and a shopfront are four places to go. The glyph
 * does the work the word cannot do at a glance -- the whole argument
 * CategoryIcon makes for the taxonomy.
 *
 * LABELS AND ICONS BOTH COME FROM exploreService. This row and the chip
 * row on the screen it opens name the same four things, and they must
 * never disagree -- the word you tapped has to be the word at the top
 * of the screen you land on. One map, imported, rather than two that
 * start identical.
 */
export function ExploreKindsCard({
  title,
  subtitle,
  kinds,
  onSelect,
}: {
  title: string;
  subtitle?: string | null;
  kinds: string[];
  onSelect: (kind: string) => void;
}) {
  const theme = useTheme();

  // THE SERVER ALREADY GUARANTEES THIS IS NON-EMPTY -- explore_kinds
  // returns None rather than a section with nothing in it. Checked
  // again here because a component that renders a titled, empty box is
  // a worse failure than one that renders nothing, and this file
  // should not depend on a promise made in another repository.
  if (kinds.length === 0) return null;

  return (
    <View style={styles.block}>
      <View style={styles.heading}>
        <Compass size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />
        <View style={styles.headingText}>
          <Text
            style={[styles.title, { color: theme.colors.onSurface }]}
            numberOfLines={1}
          >
            {title}
          </Text>
          {subtitle ? (
            <Text
              style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}
              numberOfLines={1}
            >
              {subtitle}
            </Text>
          ) : null}
        </View>
      </View>

      <FlatList
        horizontal
        data={kinds}
        keyExtractor={(kind) => kind}
        showsHorizontalScrollIndicator={false}
        // alignItems: "center" IS LOAD-BEARING, NOT TIDINESS. A
        // horizontal FlatList's content container defaults to
        // align-items: stretch, so without it every chip grows to the
        // full height the list is handed and the row renders as a set
        // of enormous vertical pills. That bug shipped once already in
        // Explore's own KindChipRow; it is pinned in both places now.
        contentContainerStyle={styles.row}
        renderItem={({ item }) => {
          const Icon = iconForKind(item);
          return (
            <Pressable
              onPress={() => onSelect(item)}
              accessibilityRole="button"
              accessibilityLabel={`Browse ${labelForKind(item)}`}
              style={({ pressed }) => [
                styles.chip,
                {
                  backgroundColor: theme.colors.surface,
                  borderColor: theme.colors.outlineVariant,
                  opacity: pressed ? 0.7 : 1,
                },
              ]}
            >
              <Icon size={16} strokeWidth={1.8} color={theme.colors.onSurfaceVariant} />
              <Text style={[styles.label, { color: theme.colors.onSurface }]}>
                {labelForKind(item)}
              </Text>
            </Pressable>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  block: { gap: spacing.sm },
  // THE HEADING IS INSET AND THE ROW IS NOT, matching Rail: the chips
  // run out to the screen edge so it is obvious there is more to the
  // right, while the title sits on the same content margin as every
  // other heading in the feed.
  heading: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
  },
  headingText: { flex: 1 },
  // THE SAME TITLE AS EVERY RAIL ABOVE IT (Rail.tsx), copied
  // deliberately rather than shared: this section is not a Rail and
  // should not import one to borrow a heading, but it must not look
  // like a different screen either.
  title: { ...typography.body, fontWeight: "800", fontSize: 17 },
  subtitle: { ...typography.bodySmall, fontSize: 12 },
  row: {
    alignItems: "center",
    paddingHorizontal: spacing.md,
    gap: spacing.sm,
  },
  // THE SAME SHAPE AS CategoryChipRow's chip AND KindChipRow's, on
  // purpose. Three rows that all narrow the market should be one
  // control wearing one outfit, not three that drifted apart.
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
