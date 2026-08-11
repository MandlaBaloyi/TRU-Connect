import React, { useState } from "react";
import { StyleSheet } from "react-native";
import { Users, Bell } from "lucide-react-native";
import { useTheme } from "react-native-paper";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";
import { EmptyState } from "@/components/feedback/EmptyState";

const TABS = [
  { key: "FOR_YOU", label: "For You" },
  { key: "FOLLOWING", label: "Following" },
];

/** Community — architecture-only pass, same shell as Business's.
 *  Supplier-specific content is deferred, separate work. */
export default function SupplierCommunity() {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState("FOR_YOU");

  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      <AppHeader
        variant="title-with-tabs"
        title="Community"
        rightIcon={<Bell size={20} color={theme.colors.onSurface} />}
        tabs={TABS}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        tabsAlign="columns"
      />
      <EmptyState icon={<Users size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />} message="Nothing here yet." />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({});
