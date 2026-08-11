import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";

/**
 * Nested Stack for the (onboarding) group -- needs its OWN contentStyle
 * fix, same reasoning as app/_layout.tsx's ThemedStack: this Stack is
 * its own separate navigator, so the root Stack's contentStyle fix
 * doesn't reach transitions happening INSIDE this one (Welcome ->
 * Role selection). Confirmed as the actual cause of the reported
 * "Landing/onboarding: Continue -> brief WHITE SCREEN" flash in dark
 * mode -- this was the one navigator in the whole app missing the fix.
 */
export default function OnboardingLayout() {
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
