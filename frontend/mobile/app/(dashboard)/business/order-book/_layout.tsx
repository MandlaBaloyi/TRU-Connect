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

import { typography } from "@/theme/typography";

export default function OrderBookLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        headerBackTitle: "Back",
        headerStyle: { backgroundColor: theme.colors.surface },
        headerTintColor: theme.colors.onSurface,
        headerTitleStyle: {
          fontSize: typography.h2.fontSize,
          fontWeight: typography.h2.fontWeight,
          color: theme.colors.onSurface,
        },
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
