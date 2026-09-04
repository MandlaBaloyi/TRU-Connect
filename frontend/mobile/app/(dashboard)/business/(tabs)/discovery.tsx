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

/**
 * Discovery — information + education + opportunities. Different from
 * Community: Community is relationships, Discovery is knowledge.
 * Curated, not an infinite feed — the business owner should find
 * something useful and leave.
 *
 * SHELL ONLY FOR NOW, same reasoning as Community. Real content
 * (education, TruConnect updates, opportunities, business resources)
 * plugs into this exact structure later.
 */
export default function BusinessDiscovery() {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState("ALL");

  const emptyMessage: Record<string, string> = {
    ALL: "Nothing here yet. Useful articles, updates and opportunities will show up here.",
    LEARN: "No business education content yet.",
    UPDATES: "No TruConnect updates yet.",
    OPPORTUNITIES: "No opportunities for your business yet.",
  };

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
      <EmptyState
        icon={<Compass size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
        message={emptyMessage[activeTab]}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({});
