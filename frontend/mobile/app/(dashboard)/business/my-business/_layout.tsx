import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";

export default function MyBusinessLayout() {
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
