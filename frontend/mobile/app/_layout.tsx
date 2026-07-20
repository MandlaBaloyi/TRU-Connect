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
 * NOTE: this replaces the default Expo template's root layout (which
 * rendered the demo (tabs) navigator). Run this generator with --clean to
 * also remove the now-unused app/(tabs) and app/modal.tsx demo screens.
 */
export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <StatusBar style="auto" />
          <OfflineBanner />
          <Stack screenOptions={{ headerShown: false }}>
            <Stack.Screen name="index" />
            <Stack.Screen name="(onboarding)" />
            <Stack.Screen name="(auth)" />
            <Stack.Screen name="(business)" />
            <Stack.Screen name="(dashboard)" />
          </Stack>
        </ThemeProvider>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
