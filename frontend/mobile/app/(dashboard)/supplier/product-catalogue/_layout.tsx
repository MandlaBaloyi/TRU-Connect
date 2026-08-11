import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";

/** Same contentStyle fix as every other Stack in this app -- this one
 *  was missing it too. */
export default function ProductCatalogueLayout() {
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
