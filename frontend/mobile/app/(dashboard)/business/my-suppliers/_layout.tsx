import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";

export default function MySuppliersLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        header: featureHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen name="[supplierId]/products/[productId]" options={{ title: "Product" }} />
      <Stack.Screen name="disconnected" options={{ title: "Disconnected Suppliers" }} />
    </Stack>
  );
}
