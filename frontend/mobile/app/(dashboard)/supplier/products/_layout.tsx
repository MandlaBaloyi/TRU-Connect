/**
 * Products navigation. Same theme-wiring reasoning as
 * order-book/_layout.tsx: the native Stack header is rendered by React
 * Navigation, not ScreenContainer, so it needs theme.colors passed
 * explicitly or it stays white regardless of dark mode. This is a
 * separate nested navigator, so it needs its own contentStyle too.
 */

import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";

export default function ProductsLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        header: featureHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen name="index" options={{ title: "Products" }} />
      <Stack.Screen name="add" options={{ title: "Add Product", presentation: "modal" }} />
      <Stack.Screen name="[productId]" options={{ headerShown: false }} />
    </Stack>
  );
}
