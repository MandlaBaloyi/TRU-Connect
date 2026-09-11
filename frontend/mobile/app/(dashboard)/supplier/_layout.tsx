import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";

/**
 * Same fix, same reasoning as business/_layout.tsx (which see) --
 * supplier/ also had no _layout.tsx of its own, so the transition
 * between supplier's (tabs) and product-catalogue used Expo Router's
 * unstyled default.
 *
 * NO GLOBAL VERIFICATION BANNER HERE, and it is worth saying why since
 * one briefly existed. A strip pinned above every supplier screen was
 * unmissable on day one and furniture by day three, cost vertical
 * space during the exact task the supplier is here to do, and drew
 * under the status bar on an edge-to-edge app. The state it announced
 * now lives where a supplier goes to ask the question --
 * Settings -> Supplier visibility (VerificationStatusCard) -- and
 * moves to the Home tab when Home is built.
 */
export default function SupplierSectionLayout() {
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
