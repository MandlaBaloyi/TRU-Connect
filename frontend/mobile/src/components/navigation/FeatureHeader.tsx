import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { ArrowLeft } from "lucide-react-native";
import type { NativeStackHeaderProps } from "@react-navigation/native-stack";

import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

const HEADER_HEIGHT = 56;

/**
 * Header for FEATURE / DETAIL screens (Level 3) — Loan Book, Order
 * Book, Settings, My Business, My Account, Security, the legal
 * documents, and the supplier catalogue.
 *
 * ============================================================
 * WHY THIS EXISTS — the confirmed root cause
 * ============================================================
 * This app had THREE header implementations, and that inconsistency
 * WAS the first-render header-height bug:
 *
 *   A. AppHeader (custom JS, pads from useSafeAreaInsets) — the 10
 *      primary tab screens. NEVER exhibited the bug.
 *   B. The NATIVE stack header (headerShown: true) — every feature
 *      stack. Height is measured in NATIVE code by
 *      react-native-screens; under edge-to-edge that measurement can
 *      miss the status-bar inset on the first layout pass, and the
 *      native header does NOT re-measure when a JS-side inset arrives
 *      later — only when React Navigation hands it a brand-new
 *      screenOptions object. That is exactly why changing the theme
 *      "fixed" it: new headerStyle object -> re-apply -> re-measure.
 *      native-stack does NOT expose headerStatusBarHeight (verified
 *      against the installed @react-navigation/native-stack types),
 *      so that native measurement cannot be corrected from JS.
 *   C. ScreenHeader (custom JS, NO inset handling at all) — the
 *      supplier product-catalogue screens.
 *
 * Removing the status bar's translucent/backgroundColor props (the
 * earlier, smaller fix) did NOT resolve it, which ruled out
 * status-bar configuration and confirmed the native measurement
 * itself as the cause.
 *
 * This component converges B and C onto A's proven approach: compute
 * the top inset in JS via useSafeAreaInsets(), which is correct from
 * the very first frame because app/_layout.tsx passes
 * initialWindowMetrics to SafeAreaProvider. No native measurement, no
 * timing gap, no dependence on an unrelated re-render.
 *
 * ============================================================
 * HOW IT'S APPLIED — one line per layout, ZERO screen changes
 * ============================================================
 * Used as native-stack's `header` option, which REPLACES the native
 * header with this JS one while leaving everything else about the
 * navigator alone:
 *
 *     <Stack screenOptions={{ header: featureHeader }} />
 *
 * Each screen keeps its existing `options={{ title: "..." }}` — this
 * component reads that same title back out of props.options, so no
 * screen file needed editing and no title moved. headerShown stays
 * TRUE (the header is shown; it's just ours, not the native one).
 *
 * SWIPE-BACK AND HARDWARE BACK ARE UNAFFECTED — this replaces the
 * header view only, not the navigator's gesture handling.
 */
export function FeatureHeader({ back, options, navigation }: NativeStackHeaderProps) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();

  // Same title the native header would have shown -- read straight
  // from the screen's own options, so titles stay declared in each
  // feature's _layout.tsx exactly as before.
  const title = options.title ?? "";

  return (
    <View
      style={[
        styles.wrapper,
        {
          backgroundColor: theme.colors.surface,
          borderBottomColor: theme.colors.outlineVariant,
          paddingTop: insets.top,
        },
      ]}
    >
      <View style={[styles.row, { minHeight: HEADER_HEIGHT }]}>
        {/* `back` is provided by the navigator only when there IS
            somewhere to go back to, so a feature's root screen
            correctly shows no back arrow without needing to be told. */}
        {back ? (
          <Pressable
            onPress={navigation.goBack}
            hitSlop={12}
            style={styles.backButton}
            accessibilityRole="button"
            accessibilityLabel="Go back"
          >
            <ArrowLeft size={24} color={theme.colors.onSurface} />
          </Pressable>
        ) : (
          <View style={styles.backSpacer} />
        )}

        <Text
          style={[styles.title, { color: theme.colors.onSurface }]}
          numberOfLines={1}
          ellipsizeMode="tail"
        >
          {title}
        </Text>

        {/* Fixed-width slot keeps the title's position identical
            between screens that do and don't have a right action, and
            makes a long title truncate rather than collide.

            minWidth WIDENED from 40 to 80 -- REAL BUG FOUND after
            direct feedback: the Stock Catalogue screen puts TWO
            elements here (a cart icon plus the 3-dot menu), but this
            slot was sized for exactly one. Since the title text next
            to it is flex:1 (greedily fills remaining space), a longer
            title could squeeze this slot back down toward its old
            40px minimum -- not enough room for two icons, so they'd
            overlap or get pushed off depending on how long the
            current screen's title happened to be. 80px is enough for
            two ~40px icon buttons with no squeeze regardless of title
            length. Single-icon screens are unaffected -- flex-end
            alignment just right-aligns their one icon the same as
            before, with a little more empty space to its left. */}
        <View style={styles.rightSlot}>
          {options.headerRight?.({ tintColor: theme.colors.onSurface, canGoBack: Boolean(back) })}
        </View>
      </View>
    </View>
  );
}

/** Ready-made value for a Stack's screenOptions.header — see this
 *  file's docstring. Declared once here rather than as an inline
 *  arrow in each layout so all eight feature stacks share one
 *  identity and one implementation. */
export const featureHeader = (props: NativeStackHeaderProps) => <FeatureHeader {...props} />;

const styles = StyleSheet.create({
  wrapper: { borderBottomWidth: StyleSheet.hairlineWidth },
  row: { flexDirection: "row", alignItems: "center", paddingHorizontal: spacing.sm },
  backButton: { width: 40, height: 40, alignItems: "center", justifyContent: "center" },
  backSpacer: { width: 40 },
  title: { ...typography.h2, flex: 1, marginLeft: spacing.xs },
  rightSlot: { minWidth: 80, alignItems: "flex-end", justifyContent: "center" },
});
