import React, { createContext, useContext, useRef } from "react";
import {
  Animated,
  NativeScrollEvent,
  NativeSyntheticEvent,
  StyleSheet,
  Text as RNText,
  View,
  Pressable,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTheme } from "react-native-paper";
import { Bell, MoreVertical } from "lucide-react-native";
import { wordmark, getWordmarkColors } from "@/theme/wordmark";
import { spacing } from "@/theme/spacing";
import { palette } from "@/theme/colors";

export const BRAND_TOP_BAR_HEIGHT = 44;
const SCROLL_THRESHOLD = 8; // ignore tiny scroll jitter so the bar doesn't flicker

type TopBarScrollContextValue = {
  translateY: Animated.Value;
  onScroll: (event: NativeSyntheticEvent<NativeScrollEvent>) => void;
};

const TopBarScrollContext = createContext<TopBarScrollContextValue | null>(null);

/**
 * Wraps the primary (tabbed) dashboard layout. Owns a single shared
 * Animated.Value so BrandTopBar hides/shows in response to whichever
 * primary screen is currently scrolling -- each screen just needs to wire
 * its ScrollView/FlatList `onScroll` to `useTopBarScroll().onScroll`.
 */
export function TopBarScrollProvider({ children }: { children: React.ReactNode }) {
  const translateY = useRef(new Animated.Value(0)).current;
  const lastOffset = useRef(0);
  const barOffset = useRef(0); // 0 = shown, -BRAND_TOP_BAR_HEIGHT = hidden

  function onScroll(event: NativeSyntheticEvent<NativeScrollEvent>) {
    const currentOffset = event.nativeEvent.contentOffset.y;
    const delta = currentOffset - lastOffset.current;

    if (Math.abs(delta) < SCROLL_THRESHOLD) return;

    if (currentOffset <= 0) {
      barOffset.current = 0; // always show once back at the top
    } else if (delta > 0) {
      barOffset.current = -BRAND_TOP_BAR_HEIGHT; // scrolling down -> hide
    } else {
      barOffset.current = 0; // scrolling up -> show
    }

    lastOffset.current = currentOffset;

    Animated.timing(translateY, {
      toValue: barOffset.current,
      duration: 180,
      useNativeDriver: true,
    }).start();
  }

  return (
    <TopBarScrollContext.Provider value={{ translateY, onScroll }}>
      {children}
    </TopBarScrollContext.Provider>
  );
}

/** Screens attach this to their ScrollView/FlatList `onScroll` prop. */
export function useTopBarScroll() {
  const ctx = useContext(TopBarScrollContext);
  if (!ctx) {
    throw new Error("useTopBarScroll must be used within a TopBarScrollProvider");
  }
  return ctx;
}

type BrandTopBarProps = {
  /** Wired up later once the notifications feature exists -- optional for now. */
  onNotificationsPress?: () => void;
  /** Wired up later once we decide what lives in the overflow menu. */
  onMenuPress?: () => void;
  /** Shows a small dot on the bell when > 0. Defaults to 0 (no badge). */
  notificationCount?: number;
};

/**
 * Persistent brand chrome for the 5 primary tabs. Wordmark only -- no
 * logo, no greeting. Slides out of view on scroll-down, back in on
 * scroll-up. Mounted once per (tabs) layout, above <Tabs />.
 *
 * Theme-aware: background, divider, and wordmark colors all follow
 * light/dark mode via react-native-paper's theme -- this was the bug
 * before (hardcoded white background stayed white in dark mode).
 *
 * NOTE: this bar is position:absolute so it can float above scrolling
 * content. Screens inside the tab group should reserve top space equal
 * to BRAND_TOP_BAR_HEIGHT + safe-area inset (e.g. via ScreenContainer's
 * top padding) so content doesn't start underneath it.
 */
export function BrandTopBar({
  onNotificationsPress,
  onMenuPress,
  notificationCount = 0,
}: BrandTopBarProps) {
  const insets = useSafeAreaInsets();
  const theme = useTheme();
  const { translateY } = useTopBarScroll();
  const wordmarkColors = getWordmarkColors(theme.dark);

  return (
    <Animated.View
      style={[
        styles.container,
        {
          paddingTop: insets.top,
          height: BRAND_TOP_BAR_HEIGHT + insets.top,
          backgroundColor: theme.colors.background,
          borderBottomColor: theme.colors.surfaceVariant,
        },
        { transform: [{ translateY }] },
      ]}
    >
      <RNText style={[styles.tru, { color: wordmarkColors.tru }]}>
        Tru
        <RNText style={[styles.connect, { color: wordmarkColors.connect }]}>Connect</RNText>
      </RNText>

      <View style={styles.actions}>
        <Pressable onPress={onNotificationsPress} hitSlop={10} style={styles.iconButton}>
          <Bell size={20} color={theme.colors.onSurface} />
          {notificationCount > 0 && (
            <View style={[styles.badge, { backgroundColor: palette.danger }]} />
          )}
        </Pressable>
        <Pressable onPress={onMenuPress} hitSlop={10} style={styles.iconButton}>
          <MoreVertical size={20} color={theme.colors.onSurface} />
        </Pressable>
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    zIndex: 10,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  tru: {
    fontSize: wordmark.fontSize,
    fontWeight: wordmark.truPart.fontWeight,
    fontStyle: wordmark.truPart.fontStyle,
    letterSpacing: wordmark.letterSpacing,
  },
  connect: {
    fontWeight: wordmark.connectPart.fontWeight,
    fontStyle: wordmark.connectPart.fontStyle,
  },
  actions: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  iconButton: {
    padding: spacing.xs,
  },
  badge: {
    position: "absolute",
    top: 4,
    right: 4,
    width: 8,
    height: 8,
    borderRadius: 4,
  },
});