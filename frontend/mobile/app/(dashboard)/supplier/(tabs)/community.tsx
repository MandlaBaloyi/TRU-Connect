import React, { useEffect, useState } from "react";
import { BackHandler, Pressable, StyleSheet, Text, View } from "react-native";
import { useNavigation, useRouter } from "expo-router";
import { ArrowLeft, MoreVertical, Search, UserPlus, Users } from "lucide-react-native";
import { TextInput, useTheme } from "react-native-paper";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";
import { EmptyState } from "@/components/feedback/EmptyState";
import { MyConnectionsList } from "@/features/dashboard/shared/connections/components/MyConnectionsList";
import { InlineBusinessSearch } from "@/features/dashboard/supplier/find-business/components/InlineBusinessSearch";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

const TABS = [
  { key: "FOR_YOU", label: "For You" },
  { key: "MY_CONNECTIONS", label: "My Connections" },
];

/**
 * Community — supplier side, direct mirror of business/(tabs)/
 * community.tsx (same search-mode header, same tabs, same reasoning
 * documented there in full — not repeated here). Search now lives in
 * the top bar here too: the search icon switches this screen's own
 * header into search mode instead of navigating to a separately-named
 * "Find Business" destination — see InlineBusinessSearch.tsx (the
 * exact body FindBusinessScreen.tsx used to own as a full screen,
 * now embedded here).
 */
export default function SupplierCommunity() {
  const router = useRouter();
  const navigation = useNavigation();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const [activeTab, setActiveTab] = useState("FOR_YOU");
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [query, setQuery] = useState("");

  const exitSearch = () => {
    setIsSearchMode(false);
    setQuery("");
  };

  // Same real bug fix as business/(tabs)/community.tsx — see that
  // file's own comment for the full reasoning.
  useEffect(() => {
    navigation.setOptions({ tabBarStyle: isSearchMode ? { display: "none" } : undefined });
  }, [isSearchMode, navigation]);

  // Same hardware-back-button fix as business/(tabs)/community.tsx —
  // see that file's own comment for the full reasoning.
  useEffect(() => {
    if (!isSearchMode) return;
    const subscription = BackHandler.addEventListener("hardwareBackPress", () => {
      exitSearch();
      return true;
    });
    return () => subscription.remove();
  }, [isSearchMode]);

  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      {isSearchMode ? (
        <View style={[styles.searchHeaderBlock, { backgroundColor: theme.colors.surface, paddingTop: insets.top + spacing.sm }]}>
          <View style={styles.searchHeaderRow}>
            <Pressable onPress={exitSearch} hitSlop={10} accessibilityRole="button" accessibilityLabel="Close search">
              <ArrowLeft size={22} color={theme.colors.onSurface} strokeWidth={2.4} />
            </Pressable>
            <TextInput
              mode="outlined"
              placeholder="Search phone, email, or name"
              value={query}
              onChangeText={setQuery}
              autoCapitalize="none"
              autoFocus
              dense
              style={styles.searchInput}
            />
          </View>
        </View>
      ) : (
        <View style={[styles.headerBlock, { backgroundColor: theme.colors.surface }]}>
          <AppHeader
            variant="title"
            title="Community"
            compact
            showBottomBorder={false}
            secondaryRightIcon={<Search size={22} color={theme.colors.onSurface} strokeWidth={2.4} />}
            onSecondaryRightIconPress={() => setIsSearchMode(true)}
            rightIcon={<MoreVertical size={20} color={theme.colors.onSurface} strokeWidth={2.4} />}
          />

          <Pressable
            onPress={() => router.push("/supplier/find-business/invite" as any)}
            style={styles.inviteRow}
            accessibilityRole="button"
            accessibilityLabel="Invite a business"
          >
            <UserPlus size={16} color={theme.colors.primary} strokeWidth={2.4} />
            <Text style={[styles.inviteText, { color: theme.colors.primary }]}>Invite a business</Text>
          </Pressable>

          <View style={[styles.tabsRow, { borderBottomColor: theme.colors.outlineVariant }]}>
            {TABS.map((tab) => {
              const selected = tab.key === activeTab;
              return (
                <Pressable
                  key={tab.key}
                  onPress={() => setActiveTab(tab.key)}
                  style={styles.tab}
                  accessibilityRole="tab"
                  accessibilityState={{ selected }}
                  accessibilityLabel={tab.label}
                >
                  <Text
                    style={[
                      styles.tabLabel,
                      { color: selected ? theme.colors.primary : theme.colors.onSurfaceVariant },
                    ]}
                  >
                    {tab.label}
                  </Text>
                  {selected && <View style={[styles.tabIndicator, { backgroundColor: theme.colors.primary }]} />}
                </Pressable>
              );
            })}
          </View>
        </View>
      )}

      {isSearchMode ? (
        <InlineBusinessSearch query={query} />
      ) : activeTab === "MY_CONNECTIONS" ? (
        <MyConnectionsList />
      ) : (
        <EmptyState
          icon={<Users size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
          message="Nothing here yet. Activity from businesses and suppliers you're connected to will show up here."
        />
      )}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  headerBlock: {},
  searchHeaderBlock: { paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  searchHeaderRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  searchInput: { flex: 1 },
  inviteRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.xs,
    minHeight: 32,
  },
  inviteText: { ...typography.body, fontWeight: "700" },
  tabsRow: { flexDirection: "row", borderBottomWidth: StyleSheet.hairlineWidth },
  tab: { flex: 1, alignItems: "center", paddingVertical: spacing.sm },
  tabLabel: { ...typography.body, fontWeight: "700", fontSize: 16 },
  tabIndicator: { height: 3, width: "55%", borderRadius: 2, marginTop: spacing.xs },
});
