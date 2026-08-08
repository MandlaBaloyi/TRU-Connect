import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";

import { typography } from "@/theme/typography";

export default function SettingsLayout() {
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
      <Stack.Screen name="index" options={{ title: "Settings" }} />
    </Stack>
  );
}
