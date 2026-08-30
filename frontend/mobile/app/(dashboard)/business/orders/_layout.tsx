import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";

/** Top-level wrapper only -- [supplierId] manages its own nested
 *  stack (cart -> delivery & payment -> review -> placed) via its own
 *  _layout.tsx. */
export default function OrdersLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        header: featureHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen name="[supplierId]" options={{ headerShown: false }} />
    </Stack>
  );
}
