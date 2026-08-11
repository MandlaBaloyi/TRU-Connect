import React from "react";
import { StyleSheet } from "react-native";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";

/** Home — architecture-only pass, same header as Business's Home.
 *  Content deferred, matching the shared-foundation approach. */
export default function SupplierDashboardHome() {
  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      <AppHeader variant="brand" />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({});
