import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { ChevronLeft, ChevronRight } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

/**
 * A fixed window of nearby pages (current ± 2) plus Previous/Next --
 * deliberately the simpler of the two pager shapes discussed (the
 * other being "1 2 3 … 42" with a jump-to-last). A catalogue realistic
 * for this app doesn't need jump-to-end complexity, and this is
 * genuinely simpler to get right.
 *
 * Renders nothing at all when there's only one page -- a pager with a
 * single, permanently-disabled "1" button isn't useful, it's clutter.
 */
export function CatalogPager({ page, totalPages, onPageChange }: Props) {
  const theme = useTheme();

  if (totalPages <= 1) return null;

  const windowStart = Math.max(1, page - 2);
  const windowEnd = Math.min(totalPages, page + 2);
  const pages: number[] = [];
  for (let p = windowStart; p <= windowEnd; p++) pages.push(p);

  return (
    <View style={styles.row}>
      <Pressable
        onPress={() => onPageChange(page - 1)}
        disabled={page === 1}
        style={[styles.arrow, page === 1 && styles.disabled]}
        accessibilityRole="button"
        accessibilityLabel="Previous page"
      >
        <ChevronLeft size={18} color={theme.colors.onSurface} strokeWidth={2} />
      </Pressable>

      {pages.map((p) => {
        const isCurrent = p === page;
        return (
          <Pressable
            key={p}
            onPress={() => onPageChange(p)}
            style={[
              styles.pageButton,
              { borderColor: theme.colors.outline },
              isCurrent && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
            ]}
            accessibilityRole="button"
            accessibilityLabel={`Page ${p}`}
            accessibilityState={{ selected: isCurrent }}
          >
            <Text style={[styles.pageLabel, { color: isCurrent ? theme.colors.onPrimary : theme.colors.onSurface }]}>
              {p}
            </Text>
          </Pressable>
        );
      })}

      <Pressable
        onPress={() => onPageChange(page + 1)}
        disabled={page === totalPages}
        style={[styles.arrow, page === totalPages && styles.disabled]}
        accessibilityRole="button"
        accessibilityLabel="Next page"
      >
        <ChevronRight size={18} color={theme.colors.onSurface} strokeWidth={2} />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: spacing.xs, paddingVertical: spacing.md },
  arrow: { padding: spacing.xs },
  disabled: { opacity: 0.3 },
  pageButton: {
    minWidth: 36,
    minHeight: 36,
    borderRadius: radius.pill,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 4,
  },
  pageLabel: { ...typography.bodySmall, fontWeight: "700" },
});
