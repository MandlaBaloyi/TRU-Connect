/**
 * Nested layout for products/[productId]/ -- this segment grew from a
 * single file (product detail) into a folder (detail + edit) once Edit
 * Product needed its own route. Same theme-wiring reasoning as the
 * parent products/_layout.tsx; this nested Stack owns its own header
 * now, so the PARENT's Stack.Screen entry for "[productId]" sets
 * headerShown: false to avoid stacking two headers.
 */

import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";

export default function ProductDetailLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        header: featureHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen name="index" options={{ title: "Product" }} />
      <Stack.Screen name="edit" options={{ title: "Edit Product", presentation: "modal" }} />
    </Stack>
  );
}
