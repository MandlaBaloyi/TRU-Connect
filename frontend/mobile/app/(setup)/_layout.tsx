import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";

/**
 * The three mandatory setup steps, between OTP and the dashboard.
 *
 * NO HEADER AND NO BACK GESTURE. The steps are independent writes, so
 * "back" would mean re-saving a section that is already saved -- and a
 * flow with a gate behind it that a person can swipe backwards out of
 * is a way to land on a blank screen behind their own dashboard.
 * Progress is shown by SetupStepScaffold's dots instead, which is the
 * information a back button was standing in for.
 *
 * ITS OWN contentStyle, for the same reason (onboarding)/_layout.tsx
 * has one: a nested Stack is a separate navigator, so the root Stack's
 * fix does not reach transitions happening inside this one, and the
 * symptom is a white flash between steps in dark mode.
 */
export default function SetupLayout() {
  const theme = useTheme();
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        gestureEnabled: false,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    />
  );
}
