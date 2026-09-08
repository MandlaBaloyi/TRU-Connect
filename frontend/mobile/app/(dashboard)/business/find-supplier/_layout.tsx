import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { communityHeader } from "@/features/dashboard/business/community/components/header/CommunityHeader";

export default function FindSupplierLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        header: communityHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen name="[supplierId]" options={{ title: "Supplier" }} />
      <Stack.Screen name="products/[supplierId]" options={{ title: "Stock Catalogue" }} />
      <Stack.Screen name="invite" options={{ title: "Invite Supplier" }} />
    </Stack>
  );
}
