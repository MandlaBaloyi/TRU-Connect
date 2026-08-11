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

/**
 * Community — business networking + relationships + relevant activity,
 * centred on existing supplier relationships. NOT a social feed —
 * short, relevant, business-focused, low-friction.
 *
 * SHELL ONLY FOR NOW: header, sub-tabs, empty state, spacing,
 * scrolling, navigation, component architecture — no manufactured
 * content. There's no supplier-activity backend yet to populate this
 * for real; an honest empty state beats fake data. Real content
 * (supplier activity, orders, relationships, updates) plugs into this
 * exact structure later.
 */
export default function BusinessCommunity() {
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
      <EmptyState
        icon={<Users size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
        message={
          activeTab === "FOR_YOU"
            ? "Nothing here yet. Activity from your business network will show up here."
            : "You're not following anyone yet. Suppliers and businesses you follow will show up here."
        }
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({});
