import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { featureHeader } from "@/components/navigation/FeatureHeader";

/** The real checkout flow, one screen per step -- cart -> delivery &
 *  payment -> review -> placed. Each screen sets its own title via
 *  navigation.setOptions where it needs to be dynamic (the cart
 *  screen's own supplier name); the rest use a fixed title here. */
export default function SupplierOrdersLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        header: featureHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen name="index" options={{ title: "Cart" }} />
      <Stack.Screen name="delivery-payment" options={{ title: "Delivery & Payment" }} />
      <Stack.Screen name="review" options={{ title: "Review Order" }} />
      <Stack.Screen name="placed" options={{ title: "Order Placed", headerBackVisible: false }} />
    </Stack>
  );
}
