import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { ChevronRight, Compass } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { labelForKind } from "../../explore/services/exploreService";

/**
 * The last thing in the feed: the ways into Explore.
 *
 * A COLUMN, NOT A RAIL, AND THAT IS THE POINT. Every other section on
 * this screen scrolls sideways, because each is a preview of a longer
 * list and the horizontal gesture says "there is more of this". These
 * are not previews of anything -- there are four of them, that is all
 * there will ever be, and hiding the fourth off the right edge would
 * be the one place in this feed where sideways scrolling conceals
 * something finite rather than sampling something long.
 *
 * It also reads correctly for where it sits. A vertical list of full
 * width rows at the bottom of a scroll is a menu, and a menu is
 * exactly what somebody who reached the end of the feed is looking
 * for.
 *
 * LABELS COME FROM labelForKind, WHICH LIVES WITH EXPLORE. Both this
 * row and Explore's own chip row name the same four things, and they
 * must never disagree -- the word you tapped has to be the word at the
 * top of the screen you land on. One map, imported, rather than two
 * that start identical.
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
          <Text style={[styles.title, { color: theme.colors.onSurface }]}>{title}</Text>
          {subtitle ? (
            <Text style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}>
              {subtitle}
            </Text>
          ) : null}
        </View>
      </View>

      <View
        style={[
          styles.list,
          { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant },
        ]}
      >
        {kinds.map((kind, index) => (
          <Pressable
            key={kind}
            onPress={() => onSelect(kind)}
            accessibilityRole="button"
            accessibilityLabel={`Browse ${labelForKind(kind)}`}
            style={({ pressed }) => [
              styles.row,
              index > 0 && { borderTopWidth: StyleSheet.hairlineWidth },
              { borderTopColor: theme.colors.outlineVariant },
              pressed && { backgroundColor: theme.colors.surfaceVariant },
            ]}
          >
            <Text style={[styles.rowLabel, { color: theme.colors.onSurface }]}>
              {labelForKind(kind)}
            </Text>
            <ChevronRight size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />
          </Pressable>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  block: { paddingHorizontal: spacing.md, gap: spacing.sm },
  heading: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  headingText: { flex: 1 },
  // THE SAME TITLE AS EVERY RAIL ABOVE IT (Rail.tsx), copied
  // deliberately rather than shared: this section is not a Rail and
  // should not import one to borrow a heading, but it must not look
  // like a different screen either.
  title: { ...typography.body, fontWeight: "800", fontSize: 17 },
  subtitle: { ...typography.bodySmall, fontSize: 12 },
  list: {
    borderRadius: radius.lg,
    borderWidth: StyleSheet.hairlineWidth,
    overflow: "hidden",
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
  },
  rowLabel: { ...typography.body, fontWeight: "600" },
});
