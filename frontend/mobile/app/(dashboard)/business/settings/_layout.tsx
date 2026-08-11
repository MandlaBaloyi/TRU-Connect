import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";

export default function SettingsLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        // CUSTOM JS HEADER instead of the native one -- this is the
        // fix for the first-render header-height bug. See
        // src/components/navigation/FeatureHeader.tsx for the full
        // root-cause analysis. Titles below are UNCHANGED; the custom
        // header reads them from each screen's own options.
        header: featureHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen name="index" options={{ title: "Settings" }} />

      {/* Appearance */}
      <Stack.Screen name="theme" options={{ title: "Theme" }} />

      {/* Notifications */}
      <Stack.Screen name="notifications-orders" options={{ title: "Stock order notifications" }} />
      <Stack.Screen name="notifications-community" options={{ title: "Community activity" }} />
      <Stack.Screen name="notifications-discovery" options={{ title: "Discovery & opportunities" }} />
      <Stack.Screen name="notifications-announcements" options={{ title: "TruConnect announcements" }} />

      {/* Business experience */}
      <Stack.Screen name="language" options={{ title: "Language" }} />
      <Stack.Screen name="start-screen" options={{ title: "Default start screen" }} />
      <Stack.Screen name="order-preferences" options={{ title: "Stock order preferences" }} />

      {/* Data & connectivity */}
      <Stack.Screen name="sync" options={{ title: "Sync" }} />
      <Stack.Screen name="mobile-data" options={{ title: "Mobile data usage" }} />
      <Stack.Screen name="offline-mode" options={{ title: "Offline mode" }} />
      <Stack.Screen name="storage" options={{ title: "Storage & cache" }} />

      {/* Privacy */}
      <Stack.Screen name="business-visibility" options={{ title: "Business visibility" }} />
      <Stack.Screen name="privacy-community" options={{ title: "Community activity" }} />
      <Stack.Screen name="data-usage" options={{ title: "Data usage" }} />
      <Stack.Screen name="personalisation" options={{ title: "Personalisation" }} />

      {/* Support & information */}
      <Stack.Screen name="help" options={{ title: "Help & support" }} />
      <Stack.Screen name="report-problem" options={{ title: "Report a problem" }} />
      <Stack.Screen name="privacy-policy" options={{ title: "Privacy policy" }} />
      <Stack.Screen name="terms" options={{ title: "Terms of service" }} />
      <Stack.Screen name="about" options={{ title: "About TruConnect" }} />
    </Stack>
  );
}
