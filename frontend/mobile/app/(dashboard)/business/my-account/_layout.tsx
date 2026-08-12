import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";

export default function MyAccountLayout() {
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
      <Stack.Screen name="index" options={{ title: "My Account" }} />
      <Stack.Screen name="edit-phone" options={{ title: "Phone number" }} />
      <Stack.Screen name="edit-email" options={{ title: "Email address" }} />
      <Stack.Screen name="bio" options={{ title: "About you" }} />
      <Stack.Screen name="verification" options={{ title: "Verification" }} />
      <Stack.Screen name="payment-methods" options={{ title: "Payment methods" }} />
      <Stack.Screen name="card-payments" options={{ title: "Card & gateway payments" }} />
      <Stack.Screen name="add-payment-method" options={{ title: "Add payment method" }} />
      <Stack.Screen name="profile-image" options={{ title: "Profile photo" }} />
      <Stack.Screen name="account-status" options={{ title: "Account status" }} />
      <Stack.Screen name="deactivate-account" options={{ title: "Deactivate account" }} />
      <Stack.Screen name="delete-account" options={{ title: "Delete account" }} />
    </Stack>
  );
}
