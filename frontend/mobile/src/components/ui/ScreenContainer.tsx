import React from "react";
import { StyleSheet, View, ViewStyle } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { SafeAreaScreen } from "./SafeAreaScreen";
import { BRAND_TOP_BAR_HEIGHT } from "@/components/navigation/BrandTopBar";
import { spacing } from "@/theme/spacing";

interface ScreenContainerProps {
  /** Optional -- screens like Community/Discovery/More are intentionally
   *  empty placeholders until their features ship. */
  children?: React.ReactNode;
  style?: ViewStyle;
  paddingHorizontal?: number;
  /**
   * Set true for screens that sit inside a (tabs) group under the
   * floating BrandTopBar (Home/Account/Community/Discovery/More) so
   * content doesn't start underneath it. Leave false (default) for
   * feature/stack screens that use ScreenHeader instead -- those
   * aren't under BrandTopBar and don't need the offset.
   */
  offsetForBrandTopBar?: boolean;
}

/**
 * Consistent screen shell: safe-area aware, themed background, standard
 * horizontal padding. Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt,
 * Section 11 (screen horizontal padding: md baseline).
 */
export function ScreenContainer({
  children,
  style,
  paddingHorizontal = spacing.md,
  offsetForBrandTopBar = false,
}: ScreenContainerProps) {
  const insets = useSafeAreaInsets();
  const topOffset = offsetForBrandTopBar ? insets.top + BRAND_TOP_BAR_HEIGHT + spacing.md : 0;

  return (
    <SafeAreaScreen>
      <View style={[styles.flex, { paddingHorizontal, paddingTop: topOffset }, style]}>
        {children}
      </View>
    </SafeAreaScreen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
});