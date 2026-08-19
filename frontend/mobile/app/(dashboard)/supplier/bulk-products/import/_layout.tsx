/**
 * Nested layout for bulk-products/import/ -- Upload and Preview are
 * two screens in one linear flow, same reason products/[productId]/
 * needed its own nested layout once it grew past one file. Same
 * theme-wiring reasoning as every other _layout.tsx in this app.
 */

import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";

export default function ImportProductsLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        header: featureHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen name="index" options={{ title: "Import Products" }} />
      <Stack.Screen name="preview" options={{ title: "Review Import" }} />
    </Stack>
  );
}
