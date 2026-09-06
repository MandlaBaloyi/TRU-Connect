import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";
import { MyAccountHeaderActions } from "@/features/dashboard/supplier/my-account/components/MyAccountHeaderActions";

export default function SupplierMyAccountLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        header: featureHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen
        name="index"
        options={{
          title: "My Account",
          headerRight: () => (
            <MyAccountHeaderActions
              profileRoute="/supplier/my-account/profile"
              qrCodeRoute="/supplier/my-account/qr-code"
            />
          ),
        }}
      />
      <Stack.Screen name="profile" options={{ title: "Profile" }} />
      <Stack.Screen name="qr-code" options={{ title: "My QR code" }} />
      <Stack.Screen name="payment-methods" options={{ title: "Payment methods" }} />
      <Stack.Screen name="add-payment-method" options={{ title: "Add payment method" }} />
      <Stack.Screen name="card-payments" options={{ title: "Card & gateway payments" }} />
      <Stack.Screen name="billing" options={{ title: "Billing" }} />
      <Stack.Screen name="subscription" options={{ title: "Subscription" }} />
      <Stack.Screen name="account-status" options={{ title: "Account status" }} />
      <Stack.Screen name="deactivate-account" options={{ title: "Deactivate account" }} />
      <Stack.Screen name="delete-account" options={{ title: "Delete account" }} />
    </Stack>
  );
}
