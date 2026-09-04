import React, { useState } from "react";
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { ClipboardCheck } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";
import { ErrorState } from "@/components/feedback/ErrorState";
import { EmptyState } from "@/components/feedback/EmptyState";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useOrders } from "../hooks/useOrders";
import { OrderCard } from "../components/OrderCard";
import { SortMenu } from "../components/SortMenu";
import type { SortOrder, StockOrderStatus } from "../types";

const TABS = [
  { key: "PENDING_SUPPLIER_APPROVAL", label: "New" },
  { key: "CONFIRMED", label: "Approved" },
  { key: "DECLINED", label: "Declined" },
];

const EMPTY_MESSAGES: Record<StockOrderStatus, string> = {
  PENDING_SUPPLIER_APPROVAL: "No orders waiting on you right now.",
  CONFIRMED: "No approved orders yet.",
  DECLINED: "No declined orders.",
};

/**
 * A supplier's own real Stock Orders home -- three real tabs (New,
 * Approved, Declined), so approving or declining an order moves it
 * to where it now genuinely belongs instead of making it vanish.
 * Confirmed directly as the real fix for a supplier receiving many
 * orders in one day: nothing disappears, everything is still exactly
 * as findable as before.
 *
 * Approved/Declined are deliberately PLAIN -- same list structure as
 * New, no extra filter row. A real date-range filter was built and
 * then removed after direct review found the chip UI genuinely
 * wasn't good; rather than leave it half-built, it (and its own
 * DateRangeFilter component and dateRange.ts utility) were removed
 * outright. The backend's own ?from=/&to= support stays in place,
 * unused for now -- ready if a real, better-designed way to filter
 * by date comes up later, not lost.
 */
export default function StockOrdersListScreen() {
  const router = useRouter();
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState<StockOrderStatus>("PENDING_SUPPLIER_APPROVAL");
  const [sortOrder, setSortOrder] = useState<SortOrder>("NEWEST");
  const { orders, isLoading, isError, refetch, isRefetching } = useOrders(activeTab, sortOrder);

  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      <AppHeader
        variant="title-with-tabs"
        title="Stock Orders"
        showBackButton
        rightIcon={<SortMenu sortOrder={sortOrder} onChange={setSortOrder} />}
        tabs={TABS}
        activeTab={activeTab}
        onTabChange={(key) => setActiveTab(key as StockOrderStatus)}
        tabsAlign="columns"
      />

      {isLoading ? (
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      ) : isError ? (
        <ErrorState message="Couldn't load your orders. Check your connection and try again." onRetry={refetch} />
      ) : orders.length === 0 ? (
        <EmptyState
          icon={<ClipboardCheck size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
          message={EMPTY_MESSAGES[activeTab]}
        />
      ) : (
        <FlatList
          data={orders}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          ListHeaderComponent={
            <Text style={[styles.count, { color: theme.colors.onSurfaceVariant }]}>
              {orders.length} {orders.length === 1 ? "order" : "orders"}
            </Text>
          }
          renderItem={({ item }) => (
            <OrderCard order={item} onPress={() => router.push(`/supplier/stock-orders/${item.id}` as any)} />
          )}
          refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={theme.colors.primary} />}
        />
      )}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  list: { paddingVertical: spacing.sm },
  count: { ...typography.bodySmall, marginHorizontal: spacing.md, marginBottom: spacing.sm },
});
