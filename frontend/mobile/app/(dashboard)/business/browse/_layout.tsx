import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";
import { communityHeader } from "@/features/dashboard/business/community/components/header/CommunityHeader";

/** Browsing stock by category. Same header as Community, because that
 *  is where every route in here is entered from. */
export default function BrowseLayout() {
  const theme = useTheme();
  return (
    <Stack
      screenOptions={{
        headerShown: true,
        header: communityHeader,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    />
  );
}
