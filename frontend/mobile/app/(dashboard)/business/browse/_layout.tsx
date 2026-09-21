import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";

/** Browsing stock by category.
 *
 *  NO NATIVE HEADER. It used to share Community's, which gave a plain
 *  back-and-title bar -- fine for a short list and wrong for this
 *  screen, where the single most useful control is a search field
 *  scoped to the category you are standing in. BrowseHeader draws its
 *  own bar with the search, the title and the offer count, so a second
 *  header above it would be two bars saying less between them. */
export default function BrowseLayout() {
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
