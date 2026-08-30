import React from "react";
import { Modal, Pressable, StyleSheet, Text } from "react-native";
import { useTheme } from "react-native-paper";
import { Check } from "lucide-react-native";

import { CATEGORY_OPTIONS } from "../../../supplier/products/types";
import type { CatalogCategoryFilter } from "../types";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  visible: boolean;
  /** The real, backend-computed list of categories THIS supplier
   *  actually has products in (useSupplierProductCategories) -- never
   *  the full platform-wide list, and never derived from whatever
   *  products happen to be loaded on the current page (that broke the
   *  moment pagination existed: the option list would shift depending
   *  on which page you were viewing). Correct regardless of
   *  page/sort/filter, since it's fetched once, independent of all
   *  three. */
  availableCategories: string[];
  selected: CatalogCategoryFilter;
  onSelect: (category: CatalogCategoryFilter) => void;
  onClose: () => void;
}

function labelFor(value: string): string {
  return CATEGORY_OPTIONS.find((option) => option.value === value)?.label ?? value;
}

/** Same bottom-sheet shape as CatalogSortSheet.tsx, deliberately --
 *  one consistent presentation for both controls on this screen,
 *  rather than Sort and Filter each inventing their own look. "All
 *  categories" is a real row here, not a separate concept from the
 *  category list -- selecting it just sets the filter back to null.
 */
export function CatalogCategoryFilterSheet({ visible, availableCategories, selected, onSelect, onClose }: Props) {
  const theme = useTheme();

  // Ordered against CATEGORY_OPTIONS' own canonical order, not raw
  // database order (which reflects nothing meaningful) -- matches the
  // same order every other category picker in this app already uses.
  const orderedCategories = CATEGORY_OPTIONS.map((option) => option.value).filter((value) =>
    availableCategories.includes(value)
  );

  return (
    <Modal visible={visible} animationType="fade" transparent onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable style={[styles.sheet, { backgroundColor: theme.colors.background }]} onPress={() => {}}>
          <Text style={[styles.title, { color: theme.colors.onSurface }]}>Filter by category</Text>
          <Pressable
            onPress={() => {
              onSelect(null);
              onClose();
            }}
            style={styles.row}
            accessibilityRole="radio"
            accessibilityState={{ checked: selected === null }}
          >
            <Text style={[styles.rowLabel, { color: theme.colors.onSurface }]}>All categories</Text>
            {selected === null && <Check size={18} color={theme.colors.primary} strokeWidth={2.5} />}
          </Pressable>
          {orderedCategories.map((category) => {
            const isSelected = category === selected;
            return (
              <Pressable
                key={category}
                onPress={() => {
                  onSelect(category);
                  onClose();
                }}
                style={styles.row}
                accessibilityRole="radio"
                accessibilityState={{ checked: isSelected }}
              >
                <Text style={[styles.rowLabel, { color: theme.colors.onSurface }]}>{labelFor(category)}</Text>
                {isSelected && <Check size={18} color={theme.colors.primary} strokeWidth={2.5} />}
              </Pressable>
            );
          })}
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.4)", justifyContent: "flex-end" },
  sheet: { borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg, padding: spacing.lg, gap: spacing.xs },
  title: { ...typography.h2, fontWeight: "700", marginBottom: spacing.sm },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    minHeight: 48,
    paddingVertical: spacing.sm,
  },
  rowLabel: { ...typography.body },
});
