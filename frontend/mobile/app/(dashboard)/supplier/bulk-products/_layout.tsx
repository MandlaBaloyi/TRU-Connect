/**
 * Bulk Products navigation. No "index" screen -- BulkProductsHomeScreen
 * was removed once it became genuinely unreachable (Products screen's
 * own shortcuts + header menu now link straight to edit/import,
 * bypassing what used to be a home screen entirely; nothing links to
 * the bare /supplier/bulk-products path anymore). Same theme-wiring
 * reasoning as order-book/_layout.tsx and products/_layout.tsx: the
 * native Stack header is rendered by React Navigation, not
 * ScreenContainer, so it needs theme.colors passed explicitly or it
 * stays white regardless of dark mode.
 */

import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";

export default function BulkProductsLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        header: featureHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen name="edit" options={{ title: "Bulk Edit" }} />
      <Stack.Screen name="import" options={{ headerShown: false }} />
    </Stack>
  );
}
