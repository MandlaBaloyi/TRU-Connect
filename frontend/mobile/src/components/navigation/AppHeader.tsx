import React from "react";
import { Pressable, StyleSheet, Text as RNText, View } from "react-native";
import { useTheme } from "react-native-paper";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Bell, MoreVertical } from "lucide-react-native";

import { getWordmarkColors } from "@/theme/wordmark";
import { palette } from "@/theme/colors";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

const HEADER_HEIGHT = 60; // within the approved 56–64dp range
const HEADER_HEIGHT_WITH_TABS = 48; // tighter — no subtitle text to make room for here

export interface AppHeaderTab {
  key: string;
  label: string;
}

type AppHeaderProps =
  | {
      /** Home only — wordmark left, bell + overflow menu right. Fixed
       *  shape (not configurable via rightIcon): no title text, no
       *  subtitle, always both icons. */
      variant: "brand";
      onNotificationsPress?: () => void;
      onMenuPress?: () => void;
      notificationCount?: number;
    }
  | {
      /** Account / More — title, optional subtitle, optional single
       *  right-side action. */
      variant: "title";
      title: string;
      subtitle?: string;
      rightIcon?: React.ReactNode;
      onRightIconPress?: () => void;
    }
  | {
      /** Community / Discovery — title row, plus a second-level tab
       *  row immediately below it.
       *
       *  tabsAlign controls how the tabs are laid out — these are
       *  genuinely different, explicitly requested looks for the two
       *  screens that use this variant, not one-size-fits-all:
       *    "spread" (default) — natural-width labels with equal GAPS
       *      between them (space-between), for Discovery's 4 tabs.
       *      With very different label lengths ("All" vs
       *      "Opportunities"), equal-width columns would make short
       *      labels float in mostly-empty space, which reads as
       *      uneven even though the columns are mathematically equal.
       *    "columns" — each tab takes an equal share of the full
       *      width (flex: 1) with its label centred inside that
       *      share, for Community's 2 tabs: "For You" centred in the
       *      left half, "Following" centred in the right half.
       */
      variant: "title-with-tabs";
      title: string;
      rightIcon?: React.ReactNode;
      onRightIconPress?: () => void;
      tabs: AppHeaderTab[];
      activeTab: string;
      onTabChange: (key: string) => void;
      tabsAlign?: "spread" | "columns";
    };

/**
 * ONE reusable header system for the 5 primary tabs (Level 1). Level 3
 * (Order Book/Loan Book/My Business detail screens) intentionally
 * stays on Expo Router's native <Stack> header — see this file's
 * previous revision's docstring for the full reasoning; unchanged
 * here.
 *
 * Background matches the bottom tab bar exactly (theme.colors.surface,
 * theme.colors.outlineVariant divider) so the top and bottom chrome
 * read as one consistent shell, not two different surfaces.
 *
 * OWNS THE STATUS-BAR SAFE-AREA REGION ITSELF: paddingTop is
 * useSafeAreaInsets().top (a real per-device measurement, never a
 * hardcoded number), added directly to THIS component's own
 * background — not left to an outer SafeAreaView to pad separately.
 * That's what actually fixes the "white strip above the header" seam:
 * previously the outer SafeAreaView auto-padded the top with
 * theme.colors.background, while this header (rendered below that
 * padding) used theme.colors.surface — two different colors stacked,
 * visible as a seam. Now there is only one background layer at the
 * top of the screen, this one, and it extends from y=0. The screens
 * that render AppHeader pass edges={["bottom","left","right"]} to
 * ScreenContainer (excluding "top") so the outer SafeAreaView doesn't
 * ALSO pad the top and double it. This works because
 * "edgeToEdgeEnabled": true in app.json makes the Android status bar a
 * translucent overlay over app content, so this header's own
 * background is what's actually visible behind the status-bar icons.
 * (It previously also depended on translucent/backgroundColor props on
 * the root <StatusBar>; those were removed as redundant under
 * edge-to-edge — see app/_layout.tsx for the full reasoning.)
 */
export function AppHeader(props: AppHeaderProps) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const wrapperStyle = [
    styles.wrapper,
    { backgroundColor: theme.colors.surface, borderBottomColor: theme.colors.outlineVariant, paddingTop: insets.top },
  ];

  if (props.variant === "brand") {
    const wordmarkColors = getWordmarkColors(theme.dark);
    return (
      <View style={wrapperStyle}>
        <View style={[styles.row, { minHeight: HEADER_HEIGHT }]}>
          <RNText style={[styles.tru, { color: wordmarkColors.tru }]}>
            Tru
            <RNText style={[styles.connect, { color: wordmarkColors.connect }]}>Connect</RNText>
          </RNText>
          <View style={styles.actions}>
            <Pressable onPress={props.onNotificationsPress} hitSlop={10} style={styles.iconButton}>
              <Bell size={20} color={theme.colors.onSurface} />
              {Boolean(props.notificationCount) && (
                <View style={[styles.badge, { backgroundColor: palette.danger }]} />
              )}
            </Pressable>
            <Pressable onPress={props.onMenuPress} hitSlop={10} style={styles.iconButton}>
              <MoreVertical size={20} color={theme.colors.onSurface} />
            </Pressable>
          </View>
        </View>
      </View>
    );
  }

  const titleRow = (
    <View
      style={[
        styles.row,
        styles.titleRow,
        { minHeight: props.variant === "title-with-tabs" ? HEADER_HEIGHT_WITH_TABS : HEADER_HEIGHT },
      ]}
    >
      <View style={styles.textWrap}>
        <RNText style={[styles.title, { color: theme.colors.onSurface }]}>{props.title}</RNText>
        {props.variant === "title" && props.subtitle && (
          <RNText style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}>{props.subtitle}</RNText>
        )}
      </View>
      {props.rightIcon && (
        <Pressable onPress={props.onRightIconPress} hitSlop={10} style={styles.iconButton}>
          {props.rightIcon}
        </Pressable>
      )}
    </View>
  );

  if (props.variant === "title") {
    return <View style={wrapperStyle}>{titleRow}</View>;
  }

  // variant === "title-with-tabs"
  const tabsAlign = props.tabsAlign ?? "spread";
  return (
    <View style={wrapperStyle}>
      {titleRow}
      <View style={[styles.tabsRow, tabsAlign === "columns" && styles.tabsRowColumns]}>
        {props.tabs.map((tab) => {
          const selected = tab.key === props.activeTab;
          return (
            <Pressable
              key={tab.key}
              onPress={() => props.onTabChange(tab.key)}
              style={[styles.tab, tabsAlign === "columns" && styles.tabColumns]}
              accessibilityRole="tab"
              accessibilityState={{ selected }}
              accessibilityLabel={tab.label}
            >
              <RNText style={[styles.tabLabel, { color: selected ? theme.colors.primary : theme.colors.onSurfaceVariant }]}>
                {tab.label}
              </RNText>
              <View style={[styles.tabUnderline, { backgroundColor: selected ? theme.colors.primary : "transparent" }]} />
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { borderBottomWidth: StyleSheet.hairlineWidth },
  row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: spacing.md },
  titleRow: { alignItems: "flex-start", paddingTop: spacing.sm },
  textWrap: { gap: 2, flexShrink: 1 },
  tru: { fontSize: 20, letterSpacing: -0.3, fontWeight: "700" },
  connect: { fontWeight: "700", fontStyle: "italic" },
  title: { ...typography.h1 },
  subtitle: { ...typography.bodySmall, fontWeight: "600", marginTop: 1 },
  actions: { flexDirection: "row", alignItems: "center" },
  iconButton: { padding: spacing.xs, marginLeft: spacing.xs },
  badge: { position: "absolute", top: 4, right: 4, width: 8, height: 8, borderRadius: 4 },
  // "fill" (default): natural-width labels, equal GAPS between them
  // (space-between) -- NOT flex:1 equal-width columns. With very
  // different label lengths ("All" vs "Opportunities"), equal-width
  // columns make short labels float in mostly-empty space while long
  // labels nearly fill their column, which visually reads as uneven
  // spacing even though the columns are mathematically equal. Equal
  // gaps between the actual text is what genuinely looks even.
  tabsRow: { flexDirection: "row", justifyContent: "space-between", paddingHorizontal: spacing.md },
  tab: { alignItems: "center", paddingVertical: spacing.sm, gap: spacing.xs },
  // "columns": each tab takes an equal share of the full width with
  // its label centred inside that share. No horizontal padding on the
  // row, so with 2 tabs each half is a true half of the screen.
  tabsRowColumns: { justifyContent: "flex-start", paddingHorizontal: 0 },
  tabColumns: { flex: 1 },
  tabLabel: { ...typography.body, fontWeight: "700" },
  tabUnderline: { height: 3, minWidth: 32, alignSelf: "stretch", borderRadius: 2 },
});
