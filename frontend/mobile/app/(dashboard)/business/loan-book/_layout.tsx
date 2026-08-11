/**
 * Loan Book navigation.
 *
 * ROUTING + THEME WIRING ONLY. Still no business logic, no calculations,
 * no API calls — but the native Stack header DOES need theme.colors,
 * because Expo Router's header is rendered by React Navigation, not by
 * ScreenContainer, so it never automatically picks up dark mode the way
 * the rest of a screen does. Without this, every Loan Book screen shows
 * a white header regardless of the device's colour scheme, unrelated to
 * whatever the screen body itself does.
 *
 * SAME REASONING APPLIES TO contentStyle, added below: this is a
 * SEPARATE nested navigator from the root Stack and the (auth) Stack --
 * it does not inherit either of their screenOptions automatically.
 * Without its own contentStyle, every Loan Book screen would show the
 * same white-flash-on-swipe-back bug in dark mode that was just fixed
 * at the root, specifically for every back-gesture inside this
 * feature (e.g. swiping back from Purchase to the main Loan Book list).
 *
 * Title text uses typography.h2 (18sp/Semibold) to match Doc 02 §4's
 * screen-title scale, rather than React Navigation's own default header
 * font.
 */

import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";

export default function LoanBookLayout() {
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
      <Stack.Screen name="index" options={{ title: "Loan Book" }} />
      <Stack.Screen name="record-sale" options={{ title: "Record Sale", presentation: "modal" }} />
      <Stack.Screen name="add-payment" options={{ title: "Record Payment", presentation: "modal" }} />
      <Stack.Screen name="[loanId]" options={{ title: "Purchase" }} />
      <Stack.Screen name="analytics" options={{ title: "Loan Analytics" }} />
      <Stack.Screen name="customer/[customerId]" options={{ title: "Customer" }} />
      <Stack.Screen name="trash" options={{ title: "Trash" }} />
      <Stack.Screen name="history" options={{ title: "Transaction History" }} />
    </Stack>
  );
}