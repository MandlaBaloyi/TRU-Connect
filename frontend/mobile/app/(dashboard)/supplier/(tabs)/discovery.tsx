import React, { useState } from "react";
import { StyleSheet } from "react-native";
import { Compass, Search } from "lucide-react-native";
import { useTheme } from "react-native-paper";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";
import { EmptyState } from "@/components/feedback/EmptyState";

const TABS = [
  { key: "ALL", label: "All" },
  { key: "LEARN", label: "Learn" },
  { key: "UPDATES", label: "Updates" },
  { key: "OPPORTUNITIES", label: "Opportunities" },
];

/** Discovery — architecture-only pass, same shell as Business's.
 *  Supplier-specific content is deferred, separate work. */
export default function SupplierDiscovery() {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState("ALL");

  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      <AppHeader
        variant="title-with-tabs"
        title="Discovery"
        rightIcon={<Search size={20} color={theme.colors.onSurface} strokeWidth={2.4} />}
        tabs={TABS}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />
      <EmptyState icon={<Compass size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />} message="Nothing here yet." />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({});
