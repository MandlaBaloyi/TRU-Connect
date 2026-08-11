import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";

export default function SecurityLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        // CUSTOM JS HEADER instead of the native one -- this is the
        // fix for the first-render header-height bug. See
        // src/components/navigation/FeatureHeader.tsx for the full
        // root-cause analysis.
        header: featureHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen name="index" options={{ title: "Account Security" }} />
      <Stack.Screen name="password" options={{ title: "Password" }} />
      <Stack.Screen name="change-password" options={{ title: "Change password" }} />
      <Stack.Screen name="two-factor" options={{ title: "Two-factor authentication" }} />
      <Stack.Screen name="two-factor-authenticator" options={{ title: "Authenticator app" }} />
      <Stack.Screen name="two-factor-email" options={{ title: "Email verification" }} />
      <Stack.Screen name="biometrics" options={{ title: "Biometric sign-in" }} />
      <Stack.Screen name="trusted-devices" options={{ title: "Trusted devices" }} />
      <Stack.Screen name="active-sessions" options={{ title: "Active sessions" }} />
      <Stack.Screen name="login-activity" options={{ title: "Login activity" }} />
      <Stack.Screen name="security-alerts" options={{ title: "Security alerts" }} />
    </Stack>
  );
}
