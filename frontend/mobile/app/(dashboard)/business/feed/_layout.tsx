import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";

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
        // NO NATIVE HEADER ANYWHERE IN THIS GROUP. Every screen here
        // now draws its own AppHeader with the count and the search --
        // the product see-alls, both supplier see-alls and Explore. A
        // native bar above any of them would be two bars saying less
        // between them.
        //
        // THE TITLES BELOW ARE STILL WORTH KEEPING. They are what the
        // router knows a route is called, they show up in navigation
        // state and in any future breadcrumb, and they are the one
        // place the four route names are listed together.
        headerShown: false,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    >
      {/* THESE TITLES MUST MATCH THE RAIL TITLES IN
        business/sections.py, AND NOTHING ENFORCES THAT. The rail's
        heading is composed server-side; this header is hardcoded here.
        They drifted the first time the copy changed: the rail said
        "Popular with businesses" and tapping its arrow opened a screen
        still headed "Moving fast right now", so the same list had two
        names one tap apart.

        If you change a title in sections.py, change it here in the
        same commit. The proper fix is for the server to carry the
        title on seeAllHref the way routes.ts already carries a
        supplier's name through to keep a destination header correct on
        its first frame -- worth doing, and bigger than a rename. */}
      <Stack.Screen name="buy-it-again" options={{ title: "Reorder what you need" }} />
      <Stack.Screen name="moving-fast" options={{ title: "Popular with businesses" }} />
      <Stack.Screen name="left-off" options={{ title: "Continue stocking up" }} />
      <Stack.Screen name="stock-for-you" options={{ title: "Stock for your shop" }} />
      <Stack.Screen name="collect-near-you" options={{ title: "Collect near you" }} />
      <Stack.Screen
        name="not-ordered-yet"
        options={{ title: "Discover new suppliers" }}
      />
      {/* NOT A RAIL'S SEE-ALL, unlike its four neighbours -- Explore is
          reached from the Community tab's own menu and has no rail
          behind it. It lives in this group because it is the same kind
          of screen (a full list of suppliers, under the community
          header) and a group of its own for one route would be a
          navigator with nothing to coordinate. */}
      <Stack.Screen name="explore" options={{ title: "Explore suppliers" }} />
    </Stack>
  );
}
