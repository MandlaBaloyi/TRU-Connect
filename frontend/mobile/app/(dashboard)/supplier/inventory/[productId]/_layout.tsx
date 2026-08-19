/**
 * Nested layout for inventory/[productId]/ -- same reason
 * products/[productId]/_layout.tsx needed one: this segment holds two
 * screens (detail + adjust), not one file, so it owns its own header
 * rather than the parent Stack.Screen entry trying to.
 */

import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";

export default function InventoryDetailLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        header: featureHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen name="index" options={{ title: "Inventory" }} />
      <Stack.Screen name="adjust" options={{ title: "Adjust Stock", presentation: "modal" }} />
    </Stack>
  );
}
