import React from "react";
import { StyleSheet, View, ViewStyle } from "react-native";
import type { Edge } from "react-native-safe-area-context";
import { SafeAreaScreen } from "./SafeAreaScreen";
import { spacing } from "@/theme/spacing";

interface ScreenContainerProps {
  /** Optional -- screens like Community/Discovery/More are intentionally
   *  empty placeholders until their features ship. */
  children?: React.ReactNode;
  style?: ViewStyle;
  paddingHorizontal?: number;
  /**
   * Pass true for screens that render under a NATIVE Stack header
   * (headerShown: true in that route's _layout.tsx — Loan Book, Order
   * Book, Settings, My Business, My Account, Security, and every
   * screen pushed within them).
   *
   * WHY THIS EXISTS -- REAL BUG, NOT A STYLE PREFERENCE: without this,
   * ScreenContainer's SafeAreaView defaulted to padding ALL edges,
   * including "top". But a native header ALREADY reserves and
   * positions the content area below itself at the native layout
   * level — the content never actually touches the status bar. Adding
   * SafeAreaView's own top inset padding on top of that was pure
   * redundant padding, and it was INCONSISTENT besides: an unrelated
   * theme change (which force-updates the native header's
   * screenOptions identity — see app/_layout.tsx's own docstring on
   * this exact class of native-stack timing issue) could cause the
   * redundant top padding to appear or disappear depending on
   * something unrelated to the screen itself. Confirmed directly: Loan
   * Book, Order Book, My Business, and Settings all called
   * ScreenContainer with no edges prop, all four showing the same
   * inconsistency.
   *
   * hasNativeHeader FIXES THIS BY MAKING THE EXTRA SPACING DELIBERATE
   * INSTEAD OF ACCIDENTAL: it excludes "top" from SafeAreaView's edges
   * (removing the redundant, unreliable padding), and adds ONE fixed,
   * always-present spacing.md on top — so every native-header screen
   * gets the SAME breathing room below its header, every time,
   * regardless of theme state or render timing.
   *
   * Screens with NO header at all (auth, onboarding — headerShown:
   * false, no <AppHeader/> either) must NOT pass this: they genuinely
   * need SafeAreaView's own top padding, since nothing else reserves
   * that space for them.
   */
  hasNativeHeader?: boolean;
  /**
   * Pass edges={["bottom","left","right"]} directly for screens that
   * render their own <AppHeader> as their first child — AppHeader owns
   * the top safe-area/status-bar region itself (see its own
   * docstring). Prefer hasNativeHeader above for native-Stack-header
   * screens; this raw prop stays available for that one other case.
   */
  edges?: Edge[];
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
  hasNativeHeader = false,
  edges,
}: ScreenContainerProps) {
  const resolvedEdges = hasNativeHeader ? (["bottom", "left", "right"] as Edge[]) : edges;

  return (
    <SafeAreaScreen edges={resolvedEdges}>
      <View
        style={[
          styles.flex,
          { paddingHorizontal, paddingTop: hasNativeHeader ? spacing.md : 0 },
          style,
        ]}
      >
        {children}
      </View>
    </SafeAreaScreen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
});
