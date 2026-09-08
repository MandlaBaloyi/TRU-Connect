import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { communityHeader } from "@/features/dashboard/business/community/components/header/CommunityHeader";

export default function MySuppliersLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        header: communityHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen name="[supplierId]/products/[productId]" options={{ title: "Product" }} />
      <Stack.Screen name="disconnected" options={{ title: "Disconnected Suppliers" }} />
    </Stack>
  );
}
