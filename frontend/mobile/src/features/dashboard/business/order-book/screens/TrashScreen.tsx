/**
 * TrashScreen — everything soft-deleted, two sections. Same 7-day rule
 * as Loan Book's Trash, applied to both orders and customers here.
 */

import React from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { useTrash } from "../hooks";
import { formatItemSummary } from "../services/orderMapper";
import { TrashRow } from "../components";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";

export default function TrashScreen() {
  const theme = useTheme();
  const {
    trashedOrders,
    trashedCustomers,
    isLoading,
    isError,
    refetch,
    restoreOrder,
    isRestoringOrder,
    restoreCustomer,
    isRestoringCustomer,
  } = useTrash();

  if (isLoading) {
    return (
      <ScreenContainer>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError) {
    return (
      <ScreenContainer>
        <ErrorState message="Could not load Trash." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const isEmpty = trashedOrders.length === 0 && trashedCustomers.length === 0;

  return (
    <ScreenContainer>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={[styles.note, { color: theme.colors.onSurfaceVariant }]}>
          Items here are permanently deleted after 7 days.
        </Text>

        {isEmpty && (
          <Text style={[styles.empty, { color: theme.colors.onSurfaceVariant }]}>Trash is empty.</Text>
        )}

        {trashedOrders.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>Orders</Text>
            {trashedOrders.map(({ order, customer }) => (
              <TrashRow
                key={order.id}
                title={`${formatItemSummary(order.lineItems)} · ${customer.name} · #${order.orderNumber}`}
                deletedAt={order.deletedAt as string}
                reason={order.deletedReason}
                onRestore={() => restoreOrder(order.id)}
                isRestoring={isRestoringOrder}
              />
            ))}
          </View>
        )}

        {trashedCustomers.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>Customers</Text>
            {trashedCustomers.map(({ customer }) => (
              <TrashRow
                key={customer.id}
                title={customer.name}
                subtitle={customer.phone}
                deletedAt={customer.deletedAt as string}
                onRestore={() => restoreCustomer(customer.id)}
                isRestoring={isRestoringCustomer}
              />
            ))}
          </View>
        )}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.lg },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  note: { ...typography.bodySmall },
  section: { gap: spacing.xs },
  sectionTitle: { ...typography.h2 },
  empty: { ...typography.body, textAlign: "center", paddingVertical: spacing.xxl },
});
