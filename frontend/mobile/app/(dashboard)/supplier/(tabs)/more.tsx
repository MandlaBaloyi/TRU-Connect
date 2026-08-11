import React from "react";
import { StyleSheet } from "react-native";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";

/** More — architecture-only pass. Content (My Account/My Business/
 *  Security/Settings for suppliers) is deferred, separate work. */
export default function SupplierMore() {
  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      <AppHeader variant="title" title="More" />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({});
