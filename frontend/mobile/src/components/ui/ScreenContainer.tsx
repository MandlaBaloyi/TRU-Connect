import React from "react";
import { StyleSheet, View, ViewStyle } from "react-native";
import { SafeAreaScreen } from "./SafeAreaScreen";
import { spacing } from "@/theme/spacing";

interface ScreenContainerProps {
  children: React.ReactNode;
  style?: ViewStyle;
  paddingHorizontal?: number;
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
}: ScreenContainerProps) {
  return (
    <SafeAreaScreen>
      <View style={[styles.flex, { paddingHorizontal }, style]}>{children}</View>
    </SafeAreaScreen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
});
