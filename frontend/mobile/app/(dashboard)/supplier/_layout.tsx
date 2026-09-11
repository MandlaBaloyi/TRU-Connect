import React from "react";
import { View } from "react-native";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";

import { VerificationBanner } from "@/components/feedback/VerificationBanner";

/**
 * Same fix, same reasoning as business/_layout.tsx (which see) --
 * supplier/ also had no _layout.tsx of its own, so the transition
 * between supplier's (tabs) and product-catalogue used Expo Router's
 * unstyled default.
 *
 * AND IT IS WHERE THE VERIFICATION BANNER MOUNTS, for the same reason
 * OfflineBanner lives in app/_layout.tsx rather than on each screen:
 * mounted once here, it is present on EVERY supplier screen --
 * including the catalogue and bulk-import flows, which is exactly
 * where an unverified supplier spends their first hour building
 * things nobody can see yet.
 *
 * NOT IN (tabs)/_layout.tsx, which was the obvious-looking spot. That
 * would cover the five tabs and leave every pushed screen without it,
 * so the message would vanish precisely when a supplier went deeper
 * into the work the banner is about.
 *
 * IT RENDERS NOTHING for a verified supplier, so this wrapper costs a
 * View and one cached query for everybody else.
 */
export default function SupplierSectionLayout() {
  const theme = useTheme();
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <VerificationBanner />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: theme.colors.background },
        }}
      />
    </View>
  );
}
