import React from "react";
import { Platform, Pressable, StatusBar, StyleSheet, Text as RNText, View } from "react-native";
import { useTheme } from "react-native-paper";
import { useRouter } from "expo-router";
import { Bell, ChevronLeft, MoreVertical } from "lucide-react-native";

import { useRootSafeAreaInsets } from "@/hooks/useRootSafeAreaInsets";
import { getWordmarkColors } from "@/theme/wordmark";
import { palette } from "@/theme/colors";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

const HEADER_HEIGHT = 60; // within the approved 56–64dp range
const HEADER_HEIGHT_COMPACT = 44; // Community's compact title row — no subtitle allowance needed
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
      /** Account / More / Community — title, optional subtitle,
       *  optional right-side action(s). `secondaryRightIcon` renders
       *  to the LEFT of `rightIcon` (e.g. Community's search icon
       *  sitting left of its bell) — added for Community's "Find
       *  Supplier" quick-access entry point; optional and additive,
       *  every other "title"-variant screen is unaffected. */
      variant: "title";
      title: string;
      subtitle?: string;
      /** A glyph before the title — a category icon, a supplier avatar.
       *  Optional and additive: every existing "title" screen renders
       *  exactly as before without it. */
      titleIcon?: React.ReactNode;
      /** CENTRES THE SUBTITLE UNDER THE TITLE. Left by default, which
       *  is right for a subtitle that qualifies the title ("Draft ·
       *  edited 2h ago"). Centred suits a COUNT, which is about the
       *  screen below rather than about the title beside it. */
      subtitleAlign?: "left" | "center";
      /** Real, generic, reusable -- a screen reached by PUSH
       *  navigation (not a top-level tab) needs a way back; every
       *  existing "title"/"title-with-tabs" consumer is a top-level
       *  tab screen and never needed this until Notifications, the
       *  first pushed screen to use either variant. Renders a real
       *  ChevronLeft calling router.back(), placed before the title
       *  text itself. */
      showBackButton?: boolean;
      rightIcon?: React.ReactNode;
      onRightIconPress?: () => void;
      secondaryRightIcon?: React.ReactNode;
      onSecondaryRightIconPress?: () => void;
      /** Defaults true. Set false when this header is composed with
       *  more content directly beneath it that owns the "real" bottom
       *  border itself (e.g. Community's title row + utility row
       *  reading as ONE block) — otherwise both borders render and
       *  produce a redundant double line. Every other "title" screen
       *  (My Account, Security, Settings, More, Account) is
       *  unaffected since it's opt-out, not opt-in. */
      showBottomBorder?: boolean;
      /** Defaults false. The "title" row normally reserves extra
       *  height + top-aligns its text to leave room for an optional
       *  subtitle line. Community has no subtitle and sits directly
       *  above more of its own header content (Invite row, tabs row)
       *  — compact drops the row to a shorter, vertically-centered
       *  height instead of carrying that subtitle allowance. Every
       *  other "title" screen doesn't pass this, so is unaffected. */
      compact?: boolean;
    }
  | {
      /** Discovery — title row, plus a second-level tab row
       *  immediately below it. (Community moved OFF this variant —
       *  it now needs content, not just tabs, between its title row
       *  and its For You/Following row, so it composes "title" plus
       *  its own body content instead; see community.tsx.)
       *
       *  tabsAlign controls how the tabs are laid out — kept
       *  configurable because Discovery's 4 unevenly-sized labels
       *  ("All" vs "Opportunities") read better with natural widths
       *  and equal gaps ("spread") than forced equal columns would.
       */
      variant: "title-with-tabs";
      title: string;
      /** Same real, generic addition as "title"'s own showBackButton
       *  -- see that prop's own comment for the full reasoning. */
      showBackButton?: boolean;
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
 * OWNS THE STATUS-BAR SAFE-AREA REGION ITSELF: paddingTop comes from
 * useRootSafeAreaInsets().top (a real per-device measurement, never a
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
 *
 * ANDROID PADS FROM StatusBar.currentHeight DIRECTLY, NOT FROM A
 * SAFE-AREA PROVIDER. Diagnosed from real device logs across several
 * rounds: react-native-screens 4.26 (new in SDK 57) wraps each screen
 * in its own nested SafeAreaProvider that begins BELOW the status
 * bar, so useSafeAreaInsets() — even the root-aware version — could
 * still read a provider that correctly reports top:0 for ITS OWN
 * coordinate space, while a DIFFERENT screen's nesting depth read
 * correctly. That's real, version-specific behaviour of a library
 * this app doesn't control, not something worth continuing to chase
 * through provider layers. StatusBar.currentHeight is a single direct
 * native measurement with no provider involved at all, and it
 * reported the correct value (23.47 on the real test device) in
 * every diagnostic round regardless of what the provider chain
 * returned. iOS has no equivalent constant, so it keeps using
 * useRootSafeAreaInsets there, where this specific regression doesn't
 * apply.
 */
export function AppHeader(props: AppHeaderProps) {
  const theme = useTheme();
  const router = useRouter();
  const rootInsets = useRootSafeAreaInsets();
  // ANDROID: StatusBar.currentHeight is a direct native measurement,
  // not read through ANY SafeAreaProvider -- proven reliable across
  // every diagnostic in this investigation (always 23.47 on the test
  // device, regardless of how many nested providers react-native-
  // screens inserted). Using it directly means this header's top
  // padding can never again be wrong because of a provider-nesting
  // change in a library we don't control. iOS has no equivalent
  // native constant, so it keeps using the safe-area value there,
  // where this specific nested-provider regression doesn't apply.
  const topInset = Platform.OS === "android" ? StatusBar.currentHeight ?? 0 : rootInsets.top;
  const suppressBorder = props.variant === "title" && props.showBottomBorder === false;
  const wrapperStyle = [
    styles.wrapper,
    suppressBorder && styles.wrapperNoBorder,
    { backgroundColor: theme.colors.surface, borderBottomColor: theme.colors.outlineVariant, paddingTop: topInset },
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
              <Bell size={20} color={theme.colors.onSurface} strokeWidth={2.4} />
              {Boolean(props.notificationCount) && (
                <View style={[styles.badge, { backgroundColor: palette.danger }]}>
                  <RNText style={styles.badgeText}>
                    {props.notificationCount! > 9 ? "9+" : props.notificationCount}
                  </RNText>
                </View>
              )}
            </Pressable>
            <Pressable onPress={props.onMenuPress} hitSlop={10} style={styles.iconButton}>
              <MoreVertical size={20} color={theme.colors.onSurface} strokeWidth={2.4} />
            </Pressable>
          </View>
        </View>
      </View>
    );
  }

  const isCompact = props.variant === "title" && props.compact === true;
  const titleRow = (
    <View
      style={[
        styles.row,
        styles.titleRow,
        isCompact && styles.titleRowCompact,
        {
          minHeight: props.variant === "title-with-tabs" ? HEADER_HEIGHT_WITH_TABS : isCompact ? HEADER_HEIGHT_COMPACT : HEADER_HEIGHT,
        },
      ]}
    >
      {(props.variant === "title" || props.variant === "title-with-tabs") && props.showBackButton && (
        <Pressable
          onPress={() => router.back()}
          hitSlop={10}
          style={styles.backButton}
          accessibilityRole="button"
          accessibilityLabel="Go back"
        >
          <ChevronLeft size={26} color={theme.colors.onSurface} strokeWidth={2.8} />
        </Pressable>
      )}
      <View style={styles.textWrap}>
        <View style={styles.titleLine}>
          {props.variant === "title" && props.titleIcon ? props.titleIcon : null}
          <RNText style={[styles.title, { color: theme.colors.onSurface }]} numberOfLines={1}>
            {props.title}
          </RNText>
        </View>
        {props.variant === "title" && props.subtitle && (
          <RNText
            style={[
              styles.subtitle,
              { color: theme.colors.onSurfaceVariant },
              props.subtitleAlign === "center" && styles.subtitleCentred,
            ]}
          >
            {props.subtitle}
          </RNText>
        )}
      </View>
      {/* Grouped into ONE cluster, not two independent flex siblings —
          `row`'s justifyContent: space-between would otherwise treat
          title/search/overflow as 3 separate items and spread a gap
          between EACH of them, floating search away from the overflow
          icon instead of sitting tight beside it. */}
      {(props.rightIcon || (props.variant === "title" && props.secondaryRightIcon)) && (
        <View style={styles.actionsGroup}>
          {props.variant === "title" && props.secondaryRightIcon && (
            <Pressable onPress={props.onSecondaryRightIconPress} hitSlop={10} style={styles.iconButton}>
              {props.secondaryRightIcon}
            </Pressable>
          )}
          {props.rightIcon && (
            <Pressable onPress={props.onRightIconPress} hitSlop={10} style={styles.iconButton}>
              {props.rightIcon}
            </Pressable>
          )}
        </View>
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
  wrapperNoBorder: { borderBottomWidth: 0 },
  row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: spacing.md },
  titleRow: { alignItems: "flex-start", paddingTop: spacing.sm },
  backButton: { marginRight: spacing.xs, marginTop: 2 },
  titleRowCompact: { alignItems: "center", paddingTop: 0 },
  titleLine: { flexDirection: "row", alignItems: "center", gap: 6 },
  subtitleCentred: { textAlign: "center" },
  textWrap: { gap: 2, flexShrink: 1 },
  tru: { fontSize: 20, letterSpacing: -0.3, fontWeight: "700" },
  connect: { fontWeight: "700", fontStyle: "italic" },
  title: { ...typography.h1 },
  subtitle: { ...typography.bodySmall, fontWeight: "600", marginTop: 1 },
  actions: { flexDirection: "row", alignItems: "center" },
  actionsGroup: { flexDirection: "row", alignItems: "center" },
  iconButton: { padding: spacing.xs, marginLeft: spacing.xs },
  badge: {
    position: "absolute",
    top: 2,
    right: 2,
    minWidth: 16,
    height: 16,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 3,
  },
  badgeText: { color: "#FFFFFF", fontSize: 10, fontWeight: "700" },
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
