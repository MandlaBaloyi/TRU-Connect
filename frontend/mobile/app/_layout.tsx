import React from "react";
import { View } from "react-native";
import { Stack } from "expo-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider, initialWindowMetrics } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { useTheme } from "react-native-paper";
import { ThemeProvider } from "@/theme/ThemeProvider";
import { SettingsProvider, useSettings } from "@/features/dashboard/business/settings/hooks/SettingsProvider";
import { useColorScheme } from "@/hooks/useColorScheme";
import { queryClient } from "@/services/api/queryClient";
import { OfflineBanner } from "@/components/feedback/OfflineBanner";

/**
 * Root layout: wires up theming, safe areas, React Query, and gesture
 * handling for the whole app.
 *
 * FOUR REAL BUGS WERE TRACED TO THIS FILE (and its descendants) AND
 * FIXED HERE. Each is explained at its own fix point below rather than
 * only in this one comment, so the reasoning stays next to the code it
 * actually applies to.
 */
export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      {/*
        EXPLICIT SafeAreaProvider with initialMetrics, rather than
        relying on Expo Router's own internal provider.

        ROOT CAUSE OF THE HEADER-HEIGHT BUG: react-native-screens'
        NATIVE header (used by every feature screen's Stack --
        Loan Book, Order Book, Settings, My Business, My Account,
        Security) measures its own height using native code, not JS.
        On Android, with edge-to-edge enabled, the real status-bar
        inset isn't always available to native code on the very FIRST
        layout pass -- a well-documented timing gap, not something
        specific to this app. Crucially, that native header does NOT
        automatically re-measure when a JS-side safe-area value updates
        later; it only re-applies its geometry when React Navigation
        gives it a genuinely new screenOptions object. That's exactly
        why changing the system theme "fixed" it: an unrelated theme
        change caused headerStyle's object identity to change,
        incidentally forcing a re-measure once the real inset value had
        settled. Passing initialWindowMetrics here gives the FIRST
        render the real, already-known inset synchronously (no async
        gap to race), so the header is correct from frame one and
        doesn't depend on an unrelated re-render ever happening.
      */}
      <SafeAreaProvider initialMetrics={initialWindowMetrics}>
        <QueryClientProvider client={queryClient}>
          {/* SettingsProvider MUST wrap ThemeProvider: ThemeProvider reads
              the saved theme preference from it, so the app-wide theme
              can't resolve correctly if the settings aren't available
              above it. */}
          <SettingsProvider>
            <ThemeProvider>
              <AppShell />
            </ThemeProvider>
          </SettingsProvider>
        </QueryClientProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

/**
 * Gates real content behind settings having actually loaded from disk.
 *
 * ROOT CAUSE OF THE THEME-INITIALIZATION FLASH: SettingsProvider reads
 * the saved theme preference from AsyncStorage, which is unavoidably
 * asynchronous -- there is no synchronous read API. Before that read
 * resolves, settings.theme is the DEFAULT ("SYSTEM"). If the user had
 * previously chosen an explicit override (say, Dark, on a device whose
 * system theme is Light), the very first frame would render LIGHT
 * (the default's resolved scheme), then swap to DARK a moment later
 * once the real preference loads -- precisely the "render light theme
 * -> load saved dark theme -> switch to dark" sequence flagged as
 * something to avoid.
 *
 * FIX: don't render the real app tree until isLoaded is true. The gate
 * itself uses the DEVICE's colour scheme (available synchronously,
 * no AsyncStorage read needed) as its best guess for the brief moment
 * it's shown -- correct in the common case (no override saved yet, or
 * the saved value happens to match), and even in the rare mismatched
 * case, this gate is on screen for a single AsyncStorage read, not a
 * simulated delay -- there is no artificial timer here.
 */
function AppShell() {
  const { isLoaded } = useSettings();
  const deviceScheme = useColorScheme();

  if (!isLoaded) {
    return (
      <View style={{ flex: 1, backgroundColor: deviceScheme === "dark" ? "#111417" : "#ffffff" }} />
    );
  }

  return <ThemedStack />;
}

function ThemedStack() {
  const theme = useTheme();
  return (
    <>
      {/*
        STATUS BAR STYLE FOLLOWS THE APP'S RESOLVED THEME, NOT THE
        RAW DEVICE SETTING.

        ROOT CAUSE OF THE STATUS-BAR VISIBILITY BUG: expo-status-bar's
        style="auto" resolves its icon colour from the OS-reported
        colour scheme (Appearance/useColorScheme), NOT from this app's
        own theme.colors. Those two are usually the same value -- but
        not when the user picks an explicit Light or Dark override in
        Settings that DISAGREES with the device's system setting. In
        that case "auto" was choosing status-bar icon colour for the
        WRONG background (e.g. dark icons rendered over this app's own
        dark background -- invisible), while the app itself correctly
        used the user's chosen theme for everything else.

        FIX: read style directly from theme.dark, the same resolved
        value ThemeProvider already computed for every other surface in
        the app, so the status bar can never disagree with what's
        actually on screen.

        NO translucent / backgroundColor PROPS HERE -- DELIBERATE, AND
        THE POINT OF THIS CHANGE. This app sets
        "edgeToEdgeEnabled": true in app.json (see the android block),
        which ALREADY makes the Android status bar a translucent
        overlay over app content at the native level. Passing
        translucent/backgroundColor="transparent" on top of that is
        redundant under edge-to-edge, and is the suspected aggravator
        of the feature-header first-render height bug: those props
        mutate native window/status-bar configuration imperatively
        AFTER mount, at which point react-native-screens' NATIVE stack
        header has typically already performed its one and only
        inset-based height measurement (native-stack does not expose
        headerStatusBarHeight -- verified against the installed
        @react-navigation/native-stack types -- so that measurement is
        not overridable from JS). Letting edge-to-edge alone own the
        status-bar configuration removes that post-mount mutation.

        The primary tab headers (AppHeader) are unaffected either way:
        they pad themselves in JS from useSafeAreaInsets().top, which
        is correct from the first frame thanks to
        SafeAreaProvider initialMetrics above.
      */}
      <StatusBar style={theme.dark ? "light" : "dark"} />
      <OfflineBanner />
      <Stack
        screenOptions={{
          headerShown: false,
          /*
            ROOT CAUSE OF THE WHITE NAVIGATION FLASH (this Stack's
            share of it): React Navigation's native-stack defaults
            contentStyle to plain white when not set. That's invisible
            in light mode (white matches) but a clearly visible flash
            during any push/pop transition in dark mode, wherever it's
            missing. This was already fixed at THIS specific Stack
            level -- the remaining, now also-fixed gaps were several
            NESTED Stacks/Tabs that each needed the exact same fix
            independently, since each is its own separate navigator
            with its own separate default: (onboarding)/_layout.tsx,
            business/(tabs)/_layout.tsx, supplier/(tabs)/_layout.tsx,
            supplier/product-catalogue/_layout.tsx, and two ENTIRELY
            IMPLICIT navigators that had no _layout.tsx at all --
            (dashboard)/business/_layout.tsx and
            (dashboard)/supplier/_layout.tsx never existed, so Expo
            Router silently used its own unstyled default Stack for
            the transition between the tab group and every pushed
            feature screen (Loan Book, Order Book, Settings, My
            Business, My Account, Security) -- exactly the transitions
            reported as flashing white. Both now exist as real files
            with the same contentStyle fix.
          */
          contentStyle: { backgroundColor: theme.colors.background },
        }}
      />
    </>
  );
}
