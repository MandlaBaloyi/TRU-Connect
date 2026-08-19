/**
 * Inventory navigation. Same theme-wiring pattern as every other
 * feature's own _layout.tsx in this app.
 */

import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";

export default function InventoryLayout() {
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
      <Stack.Screen name="[productId]" options={{ headerShown: false }} />
    </Stack>
  );
}
