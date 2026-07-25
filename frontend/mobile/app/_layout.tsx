import React from "react";
import { Stack } from "expo-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { StatusBar } from "expo-status-bar";
import { ThemeProvider } from "@/theme/ThemeProvider";
import { queryClient } from "@/services/api/queryClient";
import { OfflineBanner } from "@/components/feedback/OfflineBanner";

/**
 * Root layout: wires up theming, React Query, and gesture handling for
 * the whole app, and mounts the global OfflineBanner.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Overall User Flow)
 * and docs/02_SYSTEM_UI_UX_SPECIFICATION.txt.
 *
 * Top-level routes (index, (onboarding), (auth), (dashboard)) are
 * auto-discovered from the file system -- no need to hand-list them as
 * <Stack.Screen> entries. Hand-listing them previously caused this file
 * to drift out of sync with the real folder structure (a stale
 * "(business)" entry pointed at a route group that no longer exists;
 * business now lives under (dashboard)/business, not its own top-level
 * group). Only add an explicit <Stack.Screen> here if a specific route
 * needs its own screenOptions (e.g. a modal presentation).
 */
export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <StatusBar style="auto" />
          <OfflineBanner />
          <Stack screenOptions={{ headerShown: false }} />
        </ThemeProvider>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}