import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { communityHeader } from "@/features/dashboard/business/community/components/header/CommunityHeader";

/**
 * The screens behind the feed's arrows.
 *
 * AT /business/feed/... AND NOT /business/community/..., which was the
 * first naming and would have collided: the Community TAB is already
 * (tabs)/community.tsx, so a sibling `community/` directory puts the
 * same segment in two places and leaves expo-router to guess. "feed" is
 * also the more accurate word -- these screens belong to the For You
 * feed, not to the whole Community tab, which also holds My
 * Connections.
 *
 * TITLES ARE SET HERE, NOT FETCHED, because each screen's heading is
 * fixed -- unlike a supplier or product screen, there is no entity name
 * to wait for, so there is nothing to flash.
 *
 * THE TITLES MATCH THE RAILS EXACTLY. A reader who taps "Moving fast
 * right now" and lands on a screen called something else has to work
 * out whether they arrived where they meant to.
 */
export default function CommunityDetailLayout() {
  const theme = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: true,
        header: communityHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Stack.Screen name="buy-it-again" options={{ title: "Buy it again" }} />
      <Stack.Screen name="moving-fast" options={{ title: "Moving fast right now" }} />
      <Stack.Screen name="stock-for-you" options={{ title: "Stock for your shop" }} />
      <Stack.Screen name="collect-near-you" options={{ title: "Collect near you" }} />
      <Stack.Screen
        name="not-ordered-yet"
        options={{ title: "Suppliers you haven't ordered from" }}
      />
    </Stack>
  );
}
