import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";

import { typography } from "@/theme/typography";

export default function MyBusinessLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        headerBackTitle: "Back",
        headerStyle: { backgroundColor: theme.colors.surface },
        headerTintColor: theme.colors.onSurface,
        headerTitleStyle: {
          fontSize: typography.h2.fontSize,
          fontWeight: typography.h2.fontWeight,
          color: theme.colors.onSurface,
        },
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen name="index" options={{ title: "My Business" }} />
      <Stack.Screen name="business-details" options={{ title: "Business Details" }} />
      <Stack.Screen name="contact-details" options={{ title: "Contact Details" }} />
      <Stack.Screen name="location" options={{ title: "Location" }} />
      <Stack.Screen name="trading-details" options={{ title: "Trading Details" }} />
      <Stack.Screen name="operating-history" options={{ title: "Operating History" }} />
      <Stack.Screen name="suppliers" options={{ title: "Suppliers" }} />
    </Stack>
  );
}
