import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { communityHeader } from "@/features/dashboard/business/community/components/header/CommunityHeader";

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
        header: communityHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      {/* THE PROGRESS STRIP, declared here rather than in each screen,
          so the flow's shape is stated in one place and cannot drift.
          CommunityHeader reads checkoutStep off these options and
          draws three segments filled up to it.

          The CART IS NOT STEP 1. It is where you decide WHAT to buy;
          checkout is the three steps that follow, and showing a
          progress bar over a cart a business is still filling would
          rush a decision that has no deadline. Order Placed is step 3
          and shows the bar complete, which is the point -- it is the
          only screen that can honestly say the flow is finished. */}
      <Stack.Screen name="index" options={{ title: "Cart" }} />
      <Stack.Screen
        name="delivery-payment"
        options={{ title: "Delivery & Payment", checkoutStep: 1 } as any}
      />
      <Stack.Screen name="review" options={{ title: "Review Order", checkoutStep: 2 } as any} />
      <Stack.Screen
        name="placed"
        options={{ title: "Order Placed", headerBackVisible: false, checkoutStep: 3 } as any}
      />
      {/* Not a checkout step -- it hangs off the cart's ⋮ rather than
          the cart -> delivery -> review -> placed line. It lives in
          this stack anyway because it is scoped to the same supplier
          and wants the same header; the title here is only the
          pre-load fallback, since the screen swaps in the supplier's
          avatar and name once they are known. */}
      <Stack.Screen name="history" options={{ title: "Order history" }} />
    </Stack>
  );
}
