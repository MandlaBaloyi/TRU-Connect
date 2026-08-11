import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";

/**
 * Public legal documents — Privacy Policy and Terms of Service,
 * reachable WITHOUT being signed in: from the landing/welcome screen,
 * and from both the business and supplier registration forms. This is
 * a genuinely separate route group from (dashboard)/business/settings
 * (which requires auth and is business-specific) — the actual TEXT is
 * shared from src/content/legal/ so the two never drift into two
 * different versions of the same document, but the ROUTES themselves
 * have to be different since one is reachable pre-auth and the other
 * isn't.
 *
 * headerShown: true (native back button) + contentStyle, matching
 * every other navigator in this app -- see app/_layout.tsx's own
 * docstring on why every navigator needs this set individually.
 */
export default function LegalLayout() {
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
      <Stack.Screen name="privacy-policy" options={{ title: "Privacy policy" }} />
      <Stack.Screen name="terms" options={{ title: "Terms of service" }} />
    </Stack>
  );
}
