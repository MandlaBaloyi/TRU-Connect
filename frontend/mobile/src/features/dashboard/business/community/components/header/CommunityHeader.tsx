import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { ChevronLeft } from "lucide-react-native";
import type { NativeStackHeaderProps } from "expo-router";

import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

const HEADER_HEIGHT = 56;

/**
 * The top bar for every Community screen -- supplier profile, stock
 * catalogue, product, cart, checkout, order placed, order history.
 *
 * A SIBLING OF FeatureHeader, NOT A REPLACEMENT, and deliberately
 * copies its safe-area approach rather than improving on it. That
 * component's docstring records a real, hard-won bug: the NATIVE stack
 * header measures its own height in native code, and under
 * edge-to-edge that measurement can miss the status-bar inset on the
 * first layout pass with no way to correct it from JS. Computing the
 * inset here with useSafeAreaInsets is what makes the header correct
 * on the very first frame. Any new header in this app that does not do
 * that reintroduces the bug -- so this one does exactly the same thing,
 * on purpose.
 *
 * WHAT IT ADDS over FeatureHeader, and why Community needed its own:
 *
 *   1. A CHECKOUT PROGRESS STRIP. Cart to delivery to review is three
 *      screens with no sense of how far through you are, on the one
 *      flow in the app where a business is committing money. A screen
 *      declares `checkoutStep` in its options and gets a three-segment
 *      bar under the header row.
 *
 *   2. A SUBTITLE UNDER A PLAIN TITLE, without needing a render
 *      function. FeatureHeader only supports a subtitle via a custom
 *      headerTitle component, which is right for the supplier identity
 *      bar and overkill for "Order history".
 *
 * IT STILL READS THE SAME OPTIONS -- title, headerTitle, headerRight --
 * so screens already using EntityHeaderTitle keep working untouched.
 * Swapping a stack from featureHeader to communityHeader is one line
 * in that stack's _layout and changes nothing about its screens.
 */
export function CommunityHeader({ back, options, navigation }: NativeStackHeaderProps) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();

  const title = options.title ?? "";
  const renderTitle = typeof options.headerTitle === "function" ? options.headerTitle : null;

  // Read off the screen's own options. Typed loosely because these are
  // our additions to React Navigation's option bag, which it passes
  // through untouched but knows nothing about.
  const extras = options as unknown as {
    checkoutStep?: number;
    headerSubtitle?: string;
  };

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
        {/* `back` is supplied by the navigator only when there IS
            somewhere to go back to, so a flow's first screen shows no
            arrow without being told -- and Order Placed, which sets
            headerBackVisible false, correctly shows none either. */}
        {back ? (
          <Pressable
            onPress={navigation.goBack}
            hitSlop={12}
            style={styles.backButton}
            accessibilityRole="button"
            accessibilityLabel="Go back"
          >
            <ChevronLeft size={26} color={theme.colors.onSurface} strokeWidth={2.8} />
          </Pressable>
        ) : (
          <View style={styles.backSpacer} />
        )}

        {renderTitle ? (
          <View style={styles.titleSlot}>
            {renderTitle({ children: title, tintColor: theme.colors.onSurface })}
          </View>
        ) : (
          <View style={styles.titleSlot}>
            <View style={styles.titleColumn}>
              <Text
                style={[styles.title, { color: theme.colors.onSurface }]}
                numberOfLines={1}
                ellipsizeMode="tail"
              >
                {title}
              </Text>
              {extras.headerSubtitle ? (
                <Text
                  style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}
                  numberOfLines={1}
                >
                  {extras.headerSubtitle}
                </Text>
              ) : null}
            </View>
          </View>
        )}

        {/* Wide enough for two icon buttons without squeezing -- the
            catalogue puts a cart AND a menu here, and the title beside
            it is flex:1, so a narrower slot lets a long business name
            push the icons into each other. Found on a real device. */}
        <View style={styles.rightSlot}>
          {options.headerRight?.({ tintColor: theme.colors.onSurface, canGoBack: Boolean(back) })}
        </View>
      </View>

      {extras.checkoutStep ? <CheckoutProgress step={extras.checkoutStep} /> : null}
    </View>
  );
}

/**
 * Three segments, filled up to the current step.
 *
 * A BAR RATHER THAN "STEP 2 OF 3" TEXT. This flow is used by people
 * who are not always reading closely and not always reading English
 * first -- a filling bar is understood without being read at all, and
 * it costs no header height on a narrow phone. The step is still
 * announced properly to screen readers.
 */
function CheckoutProgress({ step }: { step: number }) {
  const theme = useTheme();
  const total = 3;

  return (
    <View
      style={styles.progressRow}
      accessibilityRole="progressbar"
      accessibilityLabel={`Step ${step} of ${total}`}
    >
      {Array.from({ length: total }, (_, index) => (
        <View
          key={index}
          style={[
            styles.progressSegment,
            {
              backgroundColor:
                index < step ? theme.colors.primary : theme.colors.outlineVariant,
            },
          ]}
        />
      ))}
    </View>
  );
}

/** Ready-made value for a Stack's screenOptions.header, declared once
 *  so every Community stack shares one identity and one
 *  implementation -- same reasoning as featureHeader. */
export const communityHeader = (props: NativeStackHeaderProps) => <CommunityHeader {...props} />;

const styles = StyleSheet.create({
  wrapper: { borderBottomWidth: StyleSheet.hairlineWidth },
  row: { flexDirection: "row", alignItems: "center", paddingHorizontal: spacing.sm },
  backButton: { width: 40, height: 40, alignItems: "center", justifyContent: "center" },
  backSpacer: { width: 40 },
  titleSlot: { flex: 1, marginLeft: spacing.xs, flexDirection: "row", alignItems: "center" },
  titleColumn: { flex: 1 },
  title: { ...typography.h2 },
  subtitle: { ...typography.bodySmall, fontSize: 12, lineHeight: 15 },
  rightSlot: { minWidth: 80, alignItems: "flex-end", justifyContent: "center" },
  progressRow: { flexDirection: "row", gap: 3, paddingHorizontal: spacing.md, paddingBottom: spacing.sm },
  progressSegment: { flex: 1, height: 3, borderRadius: 2 },
});
