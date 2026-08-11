import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";

/**
 * THIS FILE DID NOT EXIST BEFORE either -- same reasoning as
 * business/_layout.tsx and supplier/_layout.tsx (which see). business/
 * and supplier/ are siblings under (dashboard)/; without this file,
 * Expo Router used its own unstyled default Stack for this layer too.
 * Added for full consistency even though no specific transition
 * crossing exactly this layer was in the reported repro steps.
 */
export default function DashboardLayout() {
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
