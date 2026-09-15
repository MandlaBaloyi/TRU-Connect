import React, { useEffect, useState } from "react";
import { BackHandler, Pressable, StyleSheet, Text, View } from "react-native";
import { useNavigation, useRouter } from "expo-router";
import { ChevronLeft, Compass, Search, Settings, UserPlus, UserX } from "lucide-react-native";
import { TextInput, useTheme } from "react-native-paper";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";
import { Card, CardSection, StatusPill } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import { useSupplierRequests } from "@/features/dashboard/business/supplier-requests/hooks/useSupplierRequests";
import { MyConnectionsList } from "@/features/dashboard/shared/connections/components/MyConnectionsList";
import { CommunityOverflowMenu } from "@/features/dashboard/shared/connections/components/CommunityOverflowMenu";
import { InlineSupplierSearch } from "@/features/dashboard/business/find-supplier/components/InlineSupplierSearch";
import { CommunityFeed } from "@/features/dashboard/business/community/components/feed/CommunityFeed";

const TABS = [
  { key: "FOR_YOU", label: "For You" },
  { key: "MY_CONNECTIONS", label: "My Connections" },
];

/**
 * Community — business networking + relationships + relevant activity,
 * centred on existing supplier relationships. NOT a social feed —
 * short, relevant, business-focused, low-friction.
 *
 * SEARCH NOW LIVES IN THE TOP BAR, per direct product feedback:
 * "Find Supplier" is no longer a separately-named destination the
 * search icon navigates to — tapping it now switches THIS screen's
 * own header into search mode (a back arrow + inline text input,
 * replacing the title/invite/tabs block entirely) and the body
 * renders InlineSupplierSearch (business/find-supplier/components/
 * InlineSupplierSearch.tsx — the exact same search logic
 * FindSupplierScreen.tsx used to own as a full screen, extracted so
 * it can be embedded here instead). The underlying
 * /business/find-supplier/[supplierId] profile route, /invite, and
 * /products routes are all unchanged — only the SEARCH ENTRY POINT
 * itself stopped being a separately-titled screen.
 *
 * "Invite a supplier" still navigates to the real
 * /business/find-supplier/invite screen — that's a real destination
 * with its own form, not something that collapses inline the way
 * search does.
 *
 * SUPPLIER REQUESTS CARD, same as before: real, only-when-nonzero.
 */
export default function BusinessCommunity() {
  const router = useRouter();
  const navigation = useNavigation();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const [activeTab, setActiveTab] = useState("FOR_YOU");
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [query, setQuery] = useState("");
  const { requests: supplierRequests } = useSupplierRequests();

  const exitSearch = () => {
    setIsSearchMode(false);
    setQuery("");
  };

  // Real bug, caught from an actual screenshot: the bottom tab bar
  // was still showing during search mode, since DashboardTabBar is
  // owned by the PARENT tab navigator, not this screen -- changing
  // THIS screen's own state alone never touches it. The standard
  // React Navigation fix: tell the navigator itself, via setOptions,
  // and DashboardTabBar now checks for exactly this signal (see that
  // component's own comment).
  useEffect(() => {
    navigation.setOptions({ tabBarStyle: isSearchMode ? { display: "none" } : undefined });
  }, [isSearchMode, navigation]);

  // Real bug, reported directly: the phone's own back button/gesture
  // returned to Home instead of Community. Root cause: "search mode"
  // is only ever local component state (isSearchMode), never an
  // actual navigation-stack entry — so the system back button, which
  // operates on the STACK, has nothing search-related to undo and
  // falls through to the tab navigator's own default behaviour
  // instead. The in-app back arrow worked correctly because it calls
  // exitSearch() directly; the system button needed to be told to do
  // the exact same thing, via Android's own BackHandler API —
  // intercepted ONLY while isSearchMode is true, and only while this
  // screen is focused, so it never swallows back presses anywhere
  // else in the app.
  useEffect(() => {
    if (!isSearchMode) return;
    const subscription = BackHandler.addEventListener("hardwareBackPress", () => {
      exitSearch();
      return true; // consumed — don't let default navigation run too
    });
    return () => subscription.remove();
  }, [isSearchMode]);

  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      {isSearchMode ? (
        <View style={[styles.searchHeaderBlock, { backgroundColor: theme.colors.surface, paddingTop: insets.top + spacing.sm }]}>
          <View style={styles.searchHeaderRow}>
            <Pressable onPress={exitSearch} hitSlop={10} accessibilityRole="button" accessibilityLabel="Close search">
              <ChevronLeft size={26} color={theme.colors.onSurface} strokeWidth={2.8} />
            </Pressable>
            <TextInput
              mode="outlined"
              placeholder="Search by business name"
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
            rightIcon={
              <CommunityOverflowMenu
                items={[
                  {
                    // BROWSING BY WHAT A SUPPLIER *IS*, as opposed to
                    // searching by name (the magnifier, left of this
                    // menu) or being shown suppliers by the feed. It
                    // is here rather than as a tab or a rail because
                    // it is an occasional, deliberate act -- "show me
                    // the wholesalers" -- not something to put in
                    // front of somebody who opened this tab to check
                    // their connections.
                    key: "explore",
                    title: "Explore Suppliers",
                    icon: ({ size, color }) => <Compass size={size} color={color} strokeWidth={2} />,
                    onPress: () => router.push("/business/feed/explore" as any),
                  },
                  {
                    key: "disconnected",
                    title: "Disconnected Suppliers",
                    icon: ({ size, color }) => <UserX size={size} color={color} strokeWidth={2} />,
                    onPress: () => router.push("/business/my-suppliers/disconnected" as any),
                  },
                  {
                    key: "settings",
                    title: "Settings",
                    icon: ({ size, color }) => <Settings size={size} color={color} strokeWidth={2} />,
                    onPress: () => router.push("/business/settings" as any),
                  },
                ]}
              />
            }
          />

          <Pressable
            onPress={() => router.push("/business/find-supplier/invite" as any)}
            style={styles.inviteRow}
            accessibilityRole="button"
            accessibilityLabel="Invite a supplier"
          >
            <UserPlus size={16} color={theme.colors.primary} strokeWidth={2.4} />
            <Text style={[styles.inviteText, { color: theme.colors.primary }]}>Invite a supplier</Text>
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
        <InlineSupplierSearch query={query} />
      ) : (
        <>
          {supplierRequests.length > 0 && (
            <View style={styles.requestsSection}>
              <CardSection>
                <Card
                  icon={(c) => <UserPlus size={20} color={c} />}
                  label="Supplier requests"
                  description={`${supplierRequests.length} supplier${supplierRequests.length === 1 ? "" : "s"} want${
                    supplierRequests.length === 1 ? "s" : ""
                  } to connect with you`}
                  status={<StatusPill label={String(supplierRequests.length)} tone="warning" />}
                  onPress={() => router.push("/business/supplier-requests" as any)}
                />
              </CardSection>
            </View>
          )}

          {activeTab === "MY_CONNECTIONS" ? (
            <MyConnectionsList
              onPressConnection={(connection) =>
                // supplierName is carried through so the catalogue's
                // top bar is right on its very first frame instead of
                // showing "Stock Catalogue" and then swapping -- see
                // SupplierCatalogScreen's own headerSupplierName note.
                router.push(
                  `/business/find-supplier/products/${connection.otherPartyId}?supplierName=${encodeURIComponent(
                    connection.name
                  )}` as any
                )
              }
            />
          ) : (
            // FOR YOU IS NOW A REAL FEED, replacing the empty state
            // that stood here. It runs on mocked data
            // (community/services/communityFeedService) because no feed
            // endpoint exists yet -- everything else on this tab still
            // talks to the real backend, so the app keeps working
            // normally while this screen is designed. See that
            // service's own docstring on why it ignores USE_MOCK_API.
            <CommunityFeed />
          )}
        </>
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
  requestsSection: { paddingHorizontal: spacing.md, paddingTop: spacing.md },
});
