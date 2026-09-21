import React from "react";
import {
  FlatList,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTheme } from "react-native-paper";
import { ArrowDownUp, Check, Store } from "lucide-react-native";

import {
  iconForKind,
  labelForKind,
} from "@/features/dashboard/business/community/explore/services/exploreService";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { BrowseFacet, BrowseSort } from "../types";

const SORT_OPTIONS: { value: BrowseSort; label: string; hint: string }[] = [
  { value: "name", label: "A–Z", hint: "Alphabetical, the same order every visit" },
  {
    value: "price_asc",
    label: "Cheapest first",
    hint: "By the lowest price any supplier asks",
  },
  {
    value: "price_desc",
    label: "Most expensive first",
    hint: "By the highest price any supplier asks",
  },
];

/**
 * The controls that turn a category into a shortlist.
 *
 * SUPPLIER KIND IS THE AXIS, AND IT REPLACED BRAND. Brand was the first
 * attempt, argued on the grounds that a shopkeeper asks for Huletts
 * rather than for "sweeteners". That is true and the chips were still
 * wrong: a category of any size has dozens of brands, White Star alone
 * carries a shelf of flours, and twenty brand chips are a second
 * scrolling problem stacked on the first. Typing "Huletts" answers the
 * brand question better than any finite row could, and the search box
 * is one tap away in the bar above.
 *
 * A CHIP ROW IS GOOD AT A SMALL CLOSED SET where each option is a
 * different KIND of answer. Four supplier kinds is exactly that, and
 * each one changes what an order looks like -- a manufacturer is a
 * different proposition from a cash-and-carry.
 *
 * THE SAME WORDS AND GLYPHS AS EXPLORE, imported rather than repeated.
 * Two rows of chips that both narrow the market must not teach two
 * vocabularies.
 *
 * ONCE "MY SUPPLIERS" IS ON, THE AXIS BECOMES WHO. The question changes
 * from "what sort of business" to "which of mine has this", because
 * that decides whether an order is one delivery or three. It also stops
 * the row vanishing for a shop whose suppliers happen to be all one
 * kind -- a control that removes the controls beside it reads as
 * breakage rather than as filtering.
 *
 * THE COUNTS OVERLAP AND DO NOT SUM TO THE HEADER, which is correct and
 * worth knowing: a product carried by both a wholesaler and a
 * distributor is counted under both, so 69 + 41 + 16 + 12 is larger
 * than 77. These are FILTERS, not a breakdown -- each chip promises
 * exactly what tapping it returns, and the header re-counts the moment
 * one is on. A partition would need every product to belong to one
 * kind, which would mean choosing a supplier on the shop's behalf.
 *
 * SORT OPENS THE SAME SHEET THE PROVINCE PICKER USES. Cycling was one
 * tap and a silent state change: the list reordered under a reader who
 * could not see what the options were or which one they had landed on.
 * This is SelectField's sheet shape for shape -- grabber, title,
 * "Choose one", and a ROUND radio per row. That convention is already
 * in this app and already learned: square means many, round means one,
 * and an empty circle says how many answers the list wants before
 * anybody taps.
 *
 * AND THE CHIP SAYS "Sort by" UNTIL SOMETHING IS CHOSEN. A chip reading
 * "A–Z" is the default wearing the clothes of a decision -- the row
 * looks like a filter is on when nothing has been touched. Once a real
 * sort is picked the chip carries that name and fills in, so it always
 * tells the truth about its own state.
 */
export function BrowseFilterBar({
  kinds,
  suppliers,
  activeKind,
  activeSupplier,
  mineOnly,
  sort,
  onToggleKind,
  onToggleSupplier,
  onToggleMine,
  onSort,
  sortOptions,
}: {
  /** Supplier kinds, when the list is category-scoped. Absent on the
   *  see-all screens: "Reorder what you need" is a shop's own history,
   *  not a slice of the market, so "what sort of business sells this"
   *  is not the question being asked there. */
  kinds?: BrowseFacet[];
  suppliers: BrowseFacet[];
  activeKind?: string | null;
  activeSupplier?: string | null;
  mineOnly?: boolean;
  sort: BrowseSort;
  onToggleKind?: (id: string) => void;
  onToggleSupplier: (id: string) => void;
  /** Absent where it would be meaningless -- every card in "Reorder
   *  what you need" is already from a supplier this shop buys from, so
   *  a "my suppliers" toggle there filters nothing. */
  onToggleMine?: () => void;
  onSort: (next: BrowseSort) => void;
  /** The orderings this list offers. The browse sorts by name and
   *  price; a see-all keeps its own ranking as the default, because
   *  that ranking is the rail's whole argument. */
  sortOptions?: { value: BrowseSort; label: string; hint: string }[];
}) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const [sheetOpen, setSheetOpen] = React.useState(false);

  // NO KINDS MEANS SUPPLIERS ARE THE ONLY AXIS, which is the see-all
  // case: those lists are not category-scoped.
  const facets = mineOnly || !kinds ? suppliers : kinds;
  const activeFacet = mineOnly || !kinds ? activeSupplier : activeKind;
  const onToggleFacet =
    mineOnly || !kinds ? onToggleSupplier : onToggleKind ?? onToggleSupplier;

  const options = sortOptions ?? SORT_OPTIONS;
  const current = options.find((option) => option.value === sort) ?? options[0];
  // "UNSORTED" IS WHATEVER THIS LIST CALLS ITS DEFAULT -- "A–Z" for a
  // category browse, "relevance" for a see-all. The chip fills in only
  // when the reader has actually chosen something.
  const sorted = sort !== options[0].value;

  const chipStyle = (active: boolean) => ({
    backgroundColor: active ? theme.colors.primary : theme.colors.surface,
    borderColor: active ? theme.colors.primary : theme.colors.outlineVariant,
  });
  const chipText = (active: boolean) => ({
    color: active ? theme.colors.onPrimary : theme.colors.onSurface,
  });

  return (
    <View style={[styles.wrap, { borderBottomColor: theme.colors.outlineVariant }]}>
      <FlatList
        horizontal
        showsHorizontalScrollIndicator={false}
        // alignItems: "center" or every chip stretches to the list's
        // full height -- a horizontal FlatList's content container
        // defaults to align-items: stretch. Shipped twice already in
        // this codebase before it was understood.
        contentContainerStyle={styles.row}
        data={facets}
        keyExtractor={(facet) => facet.id}
        ListHeaderComponent={
          <View style={styles.leading}>
            <Pressable
              onPress={() => setSheetOpen(true)}
              accessibilityRole="button"
              accessibilityLabel={`Sort by. Currently ${current.label}.`}
              style={[styles.chip, chipStyle(sorted)]}
            >
              <ArrowDownUp
                size={14}
                strokeWidth={2}
                color={sorted ? theme.colors.onPrimary : theme.colors.onSurfaceVariant}
              />
              <Text style={[styles.label, chipText(sorted)]}>
                {sorted ? current.label : "Sort by"}
              </Text>
            </Pressable>

            {onToggleMine ? (
            <Pressable
              onPress={onToggleMine}
              accessibilityRole="button"
              accessibilityState={{ selected: Boolean(mineOnly) }}
              accessibilityLabel="Only my suppliers"
              style={[styles.chip, chipStyle(Boolean(mineOnly))]}
            >
              {mineOnly ? (
                <Check size={14} strokeWidth={2.6} color={theme.colors.onPrimary} />
              ) : (
                <Store size={14} strokeWidth={2} color={theme.colors.onSurfaceVariant} />
              )}
              <Text style={[styles.label, chipText(Boolean(mineOnly))]}>My suppliers</Text>
            </Pressable>
            ) : null}

            {facets.length > 0 ? (
              <View style={[styles.divider, { backgroundColor: theme.colors.outlineVariant }]} />
            ) : null}
          </View>
        }
        renderItem={({ item }) => {
          const active = item.id === activeFacet;
          // A KIND CARRIES ITS GLYPH; A SUPPLIER DOES NOT. The four
          // kinds are a fixed vocabulary with icons that mean
          // something; a wholesaler's NAME is the identifying thing and
          // a generic shop glyph beside every one would be noise.
          const Icon = mineOnly || !kinds ? null : iconForKind(item.id);
          return (
            <Pressable
              onPress={() => onToggleFacet(item.id)}
              accessibilityRole="button"
              accessibilityState={{ selected: active }}
              style={[styles.chip, chipStyle(active)]}
            >
              {Icon ? (
                <Icon
                  size={14}
                  strokeWidth={2}
                  color={active ? theme.colors.onPrimary : theme.colors.onSurfaceVariant}
                />
              ) : null}
              <Text style={[styles.label, chipText(active)]} numberOfLines={1}>
                {mineOnly || !kinds ? item.name : labelForKind(item.id)}
              </Text>
              {/* THE COUNT IS WHY THE CHIP IS WORTH TAPPING.
                  "Wholesalers" is a guess; "Wholesalers 69" is a
                  decision -- and it is a promise, since the server
                  counts the same cards the grid will draw. */}
              <Text
                style={[
                  styles.count,
                  { color: active ? theme.colors.onPrimary : theme.colors.onSurfaceVariant },
                ]}
              >
                {item.count}
              </Text>
            </Pressable>
          );
        }}
      />

      <Modal
        visible={sheetOpen}
        animationType="slide"
        transparent
        onRequestClose={() => setSheetOpen(false)}
      >
        <Pressable style={styles.backdrop} onPress={() => setSheetOpen(false)}>
          {/* THE INNER PRESSABLE SWALLOWS THE TAP so touching the sheet
              itself does not dismiss it -- the same guard SelectField
              uses, and the reason its onPress is deliberately empty. */}
          <Pressable
            style={[
              styles.sheet,
              {
                backgroundColor: theme.colors.background,
                paddingBottom: spacing.sm + insets.bottom,
              },
            ]}
            onPress={() => {}}
          >
            <View style={[styles.grabber, { backgroundColor: theme.colors.outlineVariant }]} />
            <Text style={[styles.sheetTitle, { color: theme.colors.onSurface }]}>Sort by</Text>
            <Text style={[styles.sheetHint, { color: theme.colors.onSurfaceVariant }]}>
              Choose one
            </Text>

            <ScrollView style={styles.list} showsVerticalScrollIndicator={false}>
              {options.map((option) => {
                const selected = option.value === sort;
                return (
                  <Pressable
                    key={option.value}
                    onPress={() => {
                      onSort(option.value);
                      setSheetOpen(false);
                    }}
                    accessibilityRole="radio"
                    accessibilityState={{ checked: selected, selected }}
                    accessibilityLabel={option.label}
                    style={({ pressed }) => [
                      styles.optionRow,
                      pressed && { backgroundColor: theme.colors.surfaceVariant },
                    ]}
                  >
                    {/* ROUND, BECAUSE IT IS ONE ANSWER. Square means
                        many in this app, and the distinction does real
                        work: it answers "how many can I pick?" before a
                        single tap. */}
                    <View
                      style={[
                        styles.box,
                        {
                          borderColor: selected ? theme.colors.primary : theme.colors.outline,
                          backgroundColor: selected ? theme.colors.primary : "transparent",
                        },
                      ]}
                    >
                      {selected ? (
                        <View style={[styles.dot, { backgroundColor: theme.colors.onPrimary }]} />
                      ) : null}
                    </View>

                    <View style={styles.optionText}>
                      <Text
                        style={[
                          styles.optionLabel,
                          {
                            color: theme.colors.onSurface,
                            fontWeight: selected ? "700" : "500",
                          },
                        ]}
                      >
                        {option.label}
                      </Text>
                      {/* WHAT THE ORDER ACTUALLY IS. "Cheapest first"
                          across a category is not obviously the
                          cheapest OFFER of each product rather than the
                          cheapest product, and somebody choosing
                          between three orderings deserves the
                          sentence. */}
                      <Text style={[styles.optionHint, { color: theme.colors.onSurfaceVariant }]}>
                        {option.value === options[0].value
                          ? `${option.hint} · Default`
                          : option.hint}
                      </Text>
                    </View>
                  </Pressable>
                );
              })}
            </ScrollView>
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { borderBottomWidth: StyleSheet.hairlineWidth },
  row: {
    alignItems: "center",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    gap: spacing.xs,
  },
  leading: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  divider: { width: StyleSheet.hairlineWidth, height: 20, marginHorizontal: spacing.xs },
  // EXACTLY CategoryChipRow's AND KindChipRow's CHIP. First it was
  // 34pt and read as secondary next to the cards; then 44pt, which was
  // over-corrected and read as huge. Both attempts were somebody
  // guessing at a size this app had already decided twice -- the
  // category chips at the top of the feed and the kind chips on Explore
  // are the same forty points, and a third row that narrows a list
  // should not be a third size.
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
  // CAPPED, because a supplier is "Thohoyandou Stock House" where a
  // kind is "Retailers" -- one long chip should not push every other
  // option off the right edge.
  label: { ...typography.bodySmall, fontWeight: "700", maxWidth: 150 },
  count: { ...typography.bodySmall, fontWeight: "600", opacity: 0.75 },

  // EVERY VALUE BELOW MATCHES SelectField's SHEET. Two sheets in one
  // app that are nearly the same read as a mistake; identical ones read
  // as a convention. They should be ONE component -- this is the third
  // copy in the codebase -- and until somebody extracts it, the least
  // bad outcome is that they do not drift.
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.45)", justifyContent: "flex-end" },
  sheet: {
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    maxHeight: "80%",
  },
  grabber: {
    alignSelf: "center",
    width: 36,
    height: 4,
    borderRadius: 2,
    marginBottom: spacing.sm,
  },
  sheetTitle: { ...typography.h2, fontWeight: "700", marginLeft: spacing.sm },
  sheetHint: { ...typography.bodySmall, marginLeft: spacing.sm, marginBottom: spacing.sm },
  list: { flexGrow: 0 },
  optionRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    minHeight: 56,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.sm,
  },
  box: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 2,
    alignItems: "center",
    justifyContent: "center",
  },
  dot: { width: 8, height: 8, borderRadius: 4 },
  optionText: { flex: 1, gap: 2 },
  optionLabel: { ...typography.body },
  optionHint: { ...typography.caption },
});
