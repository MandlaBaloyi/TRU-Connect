import React from "react";
import { StyleSheet } from "react-native";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";

/**
 * Home — intentionally empty for now. Do NOT force features in here
 * just because there is available space; Home becomes the daily
 * business overview once enough business activity exists to make it
 * useful, not before.
 */
export default function BusinessDashboardHome() {
  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      <AppHeader variant="brand" />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({});
