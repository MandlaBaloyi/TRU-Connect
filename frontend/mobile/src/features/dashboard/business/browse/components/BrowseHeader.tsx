import React, { useEffect } from "react";
import { BackHandler, Platform, Pressable, StatusBar, StyleSheet, View } from "react-native";
import { useRootSafeAreaInsets } from "@/hooks/useRootSafeAreaInsets";
import { TextInput, useTheme } from "react-native-paper";
import { Search, X } from "lucide-react-native";

import { CategoryIcon } from "@/components/categories";
import { AppHeader } from "@/components/navigation/AppHeader";
import { spacing } from "@/theme/spacing";

/**
 * The top of a category browse.
 *
 * IT IS AppHeader, NOT A BESPOKE BAR. The first version of this file
 * drew its own row -- back chevron, title, count, search icon -- and it
 * looked right while being a second header in an app that already has
 * one. Every prop it needed already existed on the "title" variant:
 * title, subtitle, showBackButton, secondaryRightIcon. Building it by
 * hand bought nothing and cost a component that would drift the first
 * time the real header changed.
 *
 * SEARCH SWAPS THE WHOLE BAR, which is the pattern the Community tab
 * already uses -- AppHeader while browsing, a back-and-field row while
 * searching. Copied rather than invented so the two screens behave
 * identically: same chevron, same Paper TextInput, same spacing.
 *
 * THE COUNT IS THE SUBTITLE, and it is not a statistic. "77 products"
 * is the argument for using the controls underneath: a number that size
 * tells a reader immediately that scrolling is the wrong plan. It says
 * PRODUCTS because it counts cards -- see _card_key on why that took
 * two attempts.
 *
 * SEARCH IS SCOPED AND STAYS SCOPED. It filters within the category
 * rather than navigating, because "search within Food & Grocery" is the
 * whole point -- a global product search is a different feature, and
 * navigating would lose the category the reader chose.
 *
 * THE SYSTEM BACK BUTTON CLOSES SEARCH FIRST, and that is a bug fixed
 * once already on the Community tab. Search mode is local state, never
 * a navigation entry, so Android's back button has nothing
 * search-related to undo and falls through to popping the screen --
 * throwing the reader out of the category instead of out of the search
 * box. Intercepted only while searching.
 */
export function BrowseHeader({
  category,
  label,
  total,
  search,
  onSearch,
  noun = { one: "product", many: "products" },
}: {
  category?: string;
  label: string;
  total: number | null;
  search: string;
  onSearch: (value: string) => void;
  /** WHAT IS BEING COUNTED. A supplier list saying "14 products" is a
   *  small, constant lie on a screen whose whole subject is suppliers
   *  -- and the reader notices, because the rows underneath are
   *  plainly not products. Defaulted rather than required so the
   *  product screens read unchanged. */
  noun?: { one: string; many: string };
}) {
  const theme = useTheme();
  const rootInsets = useRootSafeAreaInsets();
  const [searching, setSearching] = React.useState(false);

  // THE SAME TOP INSET AppHeader USES, AND THE SAME REASON. Its own
  // comment is explicit: on Android the safe-area value can be measured
  // inside a nested SafeAreaProvider that begins BELOW the status bar,
  // so StatusBar.currentHeight is the only figure that is always right.
  // The search bar was using useSafeAreaInsets and therefore padded a
  // different amount from the header it replaces -- which is why the
  // strip behind the clock and the battery changed colour when search
  // opened. Two bars on one screen must agree about where the screen
  // starts.
  const topInset = Platform.OS === "android" ? StatusBar.currentHeight ?? 0 : rootInsets.top;

  const exitSearch = () => {
    setSearching(false);
    if (search) onSearch("");
  };

  useEffect(() => {
    if (!searching) return;
    const subscription = BackHandler.addEventListener("hardwareBackPress", () => {
      exitSearch();
      return true; // consumed -- do not let the screen pop as well
    });
    return () => subscription.remove();
  }, [searching, search]);

  if (searching) {
    return (
      <View
        style={[
          styles.searchHeaderBlock,
          { backgroundColor: theme.colors.surface, paddingTop: topInset + spacing.sm },
        ]}
      >
        <View style={styles.searchHeaderRow}>
          <Pressable
            onPress={exitSearch}
            hitSlop={10}
            accessibilityRole="button"
            accessibilityLabel="Cancel search"
          >
            {/* AN X, NOT A BACK CHEVRON. A chevron promises the previous
                screen and this button does not go there -- it closes
                the search and leaves you in the category. Wearing the
                wrong glyph made the control read as "leave Food &
                Grocery", which is the opposite of what it does. */}
            <X size={24} color={theme.colors.onSurface} strokeWidth={2.6} />
          </Pressable>
          <TextInput
            mode="outlined"
            placeholder={`Search in ${label}`}
            value={search}
            onChangeText={onSearch}
            autoCapitalize="none"
            autoFocus
            dense
            style={styles.searchInput}
          />
        </View>
      </View>
    );
  }

  // NO WRAPPER VIEW. AppHeader paints its own background all the way up
  // through the status-bar region -- an outer View adding a background
  // is either redundant or, if it pads at all, the second bar this
  // screen spent two rounds removing.
  return (
    <AppHeader
      variant="title"
      title={label}
      titleIcon={
        category ? (
          <CategoryIcon category={category} size={20} color={theme.colors.onSurface} />
        ) : null
      }
      // CENTRED, BECAUSE IT IS ABOUT THE SCREEN BELOW rather than
      // about the title beside it. A left-aligned count reads as a
      // qualifier on the category name; centred it reads as the size
      // of what you are looking at.
      subtitleAlign="center"
      // AN ELLIPSIS WHILE THE COUNT IS UNKNOWN, never nothing. An
      // absent subtitle means an absent LINE, so opening a category
      // drew a short bar, then a taller one a moment later -- the
      // header visibly growing under the reader's thumb as the first
      // page landed. Reserving the line keeps the bar one height for
      // the whole of its life, and "…" is honest about not knowing
      // yet rather than flashing a zero that was never true.
      subtitle={
        total === null
          ? "…"
          : `${total.toLocaleString()} ${total === 1 ? noun.one : noun.many}${
              search ? ` for “${search}”` : ""
            }`
      }
      // NO onBackPress: AppHeader's own back button calls
      // router.back(), which is exactly what this screen wants. A
      // handler passed in here would be a second way to do the same
      // thing, and the one that drifts.
      showBackButton
      compact
      secondaryRightIcon={
        <Search size={22} color={theme.colors.onSurface} strokeWidth={2.4} />
      }
      onSecondaryRightIconPress={() => setSearching(true)}
    />
  );
}

const styles = StyleSheet.create({
  // THE SAME THREE STYLES THE COMMUNITY TAB USES for its own search
  // row, copied so the two bars are the same bar. If a fourth screen
  // needs this, it is time to extract it rather than copy it again.
  searchHeaderBlock: { paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  searchHeaderRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  searchInput: { flex: 1 },
});
