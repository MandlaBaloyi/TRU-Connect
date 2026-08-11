import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";

/**
 * Same fix, same reasoning as business/_layout.tsx (which see) --
 * supplier/ also had no _layout.tsx of its own, so the transition
 * between supplier's (tabs) and product-catalogue used Expo Router's
 * unstyled default.
 */
export default function SupplierSectionLayout() {
  const theme = useTheme();
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    />
  );
}
