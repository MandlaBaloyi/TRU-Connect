/**
 * OrderBookScreen — the queue. Every pending order first, so the shop
 * owner opens the app and immediately sees what needs doing — the same
 * "what do I need to do right now" priority as Loan Book's dashboard.
 */

import React, { useState } from "react";
import { ActivityIndicator, FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { History, Trash2 } from "lucide-react-native";

import { useOrderBook, useOrderMutations, useAutoClearSweepRunner } from "../hooks";
import type { OrderStatus, OrderView } from "../types";
import { EmptyOrderBook, OrderCard, OrderSearchBar, OrderStatusFilterBar } from "../components";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SecondaryButton } from "@/components/ui/SecondaryButton";

export default function OrderBookScreen() {
  const router = useRouter();
  const theme = useTheme();

  // Runs the auto-clear check for as long as the queue screen is open —
  // see useAutoClearSweepRunner's docstring for why this is a mock-mode
  // stand-in for what becomes a real scheduled job once the backend
  // exists.
  useAutoClearSweepRunner();

  const [searchTerm, setSearchTerm] = useState("");
  const [status, setStatus] = useState<OrderStatus | undefined>(undefined);

  const filters = { status, searchTerm: searchTerm || undefined };
  const { orders, isLoading, isRefreshing, isError, isEmpty, isFilteredEmpty, refetch } =
    useOrderBook(filters);
  const { clearAllCompleted, isClearingCompleted } = useOrderMutations();

  const goToCreateOrder = () => router.push("/business/order-book/create-order");
  const goToOrder = (orderId: string) => router.push(`/business/order-book/${orderId}`);
  const clearFilters = () => {
    setSearchTerm("");
    setStatus(undefined);
  };
  const handleClearCompleted = async () => {
    await clearAllCompleted();
  };

  if (isError) {
    return (
      <ScreenContainer>
        <ErrorState message="Could not load your order book. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer>
      <FlatList<OrderView>
        data={orders}
        keyExtractor={(item) => item.order.id}
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={refetch} tintColor={theme.colors.primary} />
        }
        ListHeaderComponent={
          <View style={styles.header}>
            <View style={styles.actionRow}>
              <View style={styles.actionButton}>
                <PrimaryButton onPress={goToCreateOrder}>New order</PrimaryButton>
              </View>
              <View style={styles.actionButton}>
                <SecondaryButton onPress={() => router.push("/business/order-book/balances")}>
                  View balances
                </SecondaryButton>
              </View>
            </View>
            <OrderSearchBar value={searchTerm} onChangeText={setSearchTerm} onClear={() => setSearchTerm("")} />
            <OrderStatusFilterBar status={status} onStatusChange={setStatus} />
            {status === "COMPLETED" && orders.length > 0 && (
              <Pressable
                onPress={handleClearCompleted}
                disabled={isClearingCompleted}
                style={styles.clearCompletedButton}
                accessibilityRole="button"
                accessibilityLabel="Clear all completed orders"
              >
                <Text style={[styles.clearCompletedText, { color: theme.colors.error }]}>
                  {isClearingCompleted ? "Clearing…" : "Clear all completed"}
                </Text>
              </Pressable>
            )}
            <View style={styles.countRow}>
              {orders.length > 0 && (
                <Text style={[styles.count, { color: theme.colors.onSurfaceVariant }]}>
                  {orders.length === 1 ? "1 order" : `${orders.length} orders`}
                </Text>
              )}
              <View style={styles.utilityLinks}>
                <Pressable
                  onPress={() => router.push("/business/order-book/history")}
                  style={styles.utilityLink}
                  accessibilityRole="button"
                  accessibilityLabel="View order history"
                  hitSlop={8}
                >
                  <History size={14} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
                  <Text style={[styles.utilityLinkText, { color: theme.colors.onSurfaceVariant }]}>History</Text>
                </Pressable>
                <Pressable
                  onPress={() => router.push("/business/order-book/trash")}
                  style={styles.utilityLink}
                  accessibilityRole="button"
                  accessibilityLabel="View trash"
                  hitSlop={8}
                >
                  <Trash2 size={14} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
                  <Text style={[styles.utilityLinkText, { color: theme.colors.onSurfaceVariant }]}>Trash</Text>
                </Pressable>
              </View>
            </View>
          </View>
        }
        renderItem={({ item }) => <OrderCard view={item} onPress={() => goToOrder(item.order.id)} />}
        ItemSeparatorComponent={() => <View style={[styles.separator, { backgroundColor: theme.colors.outline }]} />}
        ListEmptyComponent={
          isLoading ? (
            <View style={styles.loading}>
              <ActivityIndicator color={theme.colors.primary} />
            </View>
          ) : isFilteredEmpty ? (
            <EmptyOrderBook variant="NO_RESULTS" onClearFilters={clearFilters} />
          ) : isEmpty ? (
            <EmptyOrderBook variant="FIRST_RUN" onCreateOrder={goToCreateOrder} />
          ) : null
        }
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: spacing.md, paddingTop: spacing.sm, paddingBottom: spacing.xxl, gap: spacing.sm },
  header: { gap: spacing.md, marginBottom: spacing.sm },
  actionRow: { flexDirection: "row", gap: spacing.sm },
  actionButton: { flex: 1 },
  countRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  count: { ...typography.bodySmall },
  clearCompletedButton: { alignSelf: "flex-start", minHeight: 32, justifyContent: "center" },
  clearCompletedText: { ...typography.bodySmall, fontWeight: "600" },
  utilityLinks: { flexDirection: "row", gap: spacing.md },
  utilityLink: { flexDirection: "row", alignItems: "center", gap: 4, minHeight: 32, paddingHorizontal: spacing.xs },
  utilityLinkText: { ...typography.bodySmall, fontWeight: "600" },
  separator: { height: StyleSheet.hairlineWidth },
  loading: { paddingVertical: spacing.xxl, alignItems: "center" },
});
