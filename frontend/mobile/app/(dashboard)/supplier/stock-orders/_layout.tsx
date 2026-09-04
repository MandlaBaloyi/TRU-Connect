import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";

/** Both screens render their own AppHeader manually (variant="title",
 *  showBackButton) -- matching how notifications/ and orders/ (business
 *  side) already do this, not the native Stack header. */
export default function SupplierStockOrdersLayout() {
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
