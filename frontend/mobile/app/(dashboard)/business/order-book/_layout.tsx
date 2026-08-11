/**
 * Order Book navigation.
 * Same theme-wiring reasoning as loan-book/_layout.tsx: the native
 * Stack header is rendered by React Navigation, not ScreenContainer, so
 * it needs theme.colors passed explicitly or it stays white regardless
 * of dark mode. This is a separate nested navigator from the root and
 * (auth) stacks, so it needs its own contentStyle too.
 */

import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";

export default function OrderBookLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        // CUSTOM JS HEADER instead of the native one -- this is the
        // fix for the first-render header-height bug. See
        // src/components/navigation/FeatureHeader.tsx for the full
        // root-cause analysis. Titles below are UNCHANGED; the custom
        // header reads them from each screen's own options.
        header: featureHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen name="index" options={{ title: "Order Book" }} />
      <Stack.Screen name="create-order" options={{ title: "New Order", presentation: "modal" }} />
      <Stack.Screen name="[orderId]" options={{ title: "Order" }} />
      <Stack.Screen name="history" options={{ title: "Order History" }} />
      <Stack.Screen name="trash" options={{ title: "Trash" }} />
      <Stack.Screen name="balances" options={{ title: "Balances" }} />
      <Stack.Screen name="performance" options={{ title: "Performance" }} />
    </Stack>
  );
}
