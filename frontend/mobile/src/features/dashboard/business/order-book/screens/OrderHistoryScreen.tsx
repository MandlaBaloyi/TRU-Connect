/**
 * OrderHistoryScreen — a simple log of what actually happened to money,
 * newest first. Deliberately narrow: only ORDER_COMPLETED and
 * ORDER_CANCELLED show up here. "Order placed," "Order restored,"
 * "New customer," etc. are real events (still recorded in the backend's
 * history table, still there if ever needed) but they're internal
 * housekeeping, not something a shop owner needs to scroll past to see
 * what they actually care about: completed and cancelled orders.
 * Flat rows under a day label, no cards — same flat-list treatment as
 * Loan Book's LoanHistoryScreen/TransactionRow.
 */

import React, { useMemo } from "react";
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { useOrderBook, useOrderHistory } from "../hooks";
import type { OrderHistoryEvent } from "../types";
import { HistoryEventRow } from "../components";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";

/** The only event types shown to the business owner — see file
 *  docstring. Add to this set if another event type ever earns a place
 *  here; nothing else about this screen needs to change to add one. */
const VISIBLE_EVENT_TYPES: ReadonlySet<OrderHistoryEvent["eventType"]> = new Set([
  "ORDER_COMPLETED",
  "ORDER_CANCELLED",
]);

function dayLabel(iso: string): string {
  const date = new Date(iso);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  const sameDay = (a: Date, b: Date) =>
    a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
  if (sameDay(date, today)) return "Today";
  if (sameDay(date, yesterday)) return "Yesterday";
  return date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

interface Row {
  type: "header" | "event";
  key: string;
  label?: string;
  event?: OrderHistoryEvent;
}

export default function OrderHistoryScreen() {
  const theme = useTheme();
  const { events, isLoading, isError, refetch } = useOrderHistory();
  const { orders } = useOrderBook();

  const customerNames = useMemo(() => {
    const map = new Map<string, string>();
    orders.forEach((view) => map.set(view.customer.id, view.customer.name));
    return map;
  }, [orders]);

  const visibleEvents = useMemo(
    () => events.filter((event) => VISIBLE_EVENT_TYPES.has(event.eventType)),
    [events]
  );

  const rows = useMemo<Row[]>(() => {
    const result: Row[] = [];
    let lastLabel: string | null = null;
    visibleEvents.forEach((event) => {
      const label = dayLabel(event.occurredAt);
      if (label !== lastLabel) {
        result.push({ type: "header", key: `header-${label}-${event.id}`, label });
        lastLabel = label;
      }
      result.push({ type: "event", key: event.id, event });
    });
    return result;
  }, [visibleEvents]);

  const isEmpty = !isLoading && visibleEvents.length === 0;

  if (isError) {
    return (
      <ScreenContainer>
        <ErrorState message="Could not load order history." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer>
      <FlatList<Row>
        data={rows}
        keyExtractor={(row) => row.key}
        contentContainerStyle={styles.content}
        renderItem={({ item }) =>
          item.type === "header" ? (
            <Text style={[styles.dayLabel, { color: theme.colors.onSurfaceVariant }]}>{item.label}</Text>
          ) : (
            <HistoryEventRow event={item.event!} customerName={customerNames.get(item.event!.customerId) ?? "Customer"} />
          )
        }
        ItemSeparatorComponent={() => <View style={[styles.separator, { backgroundColor: theme.colors.outline }]} />}
        ListEmptyComponent={
          isLoading ? (
            <View style={styles.loading}>
              <ActivityIndicator color={theme.colors.primary} />
            </View>
          ) : isEmpty ? (
            <Text style={[styles.empty, { color: theme.colors.onSurfaceVariant }]}>No activity yet.</Text>
          ) : null
        }
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: spacing.md, paddingVertical: spacing.sm, gap: 0 },
  dayLabel: { ...typography.bodySmall, fontWeight: "600", marginTop: spacing.md, marginBottom: spacing.xs },
  separator: { height: StyleSheet.hairlineWidth },
  loading: { paddingVertical: spacing.xxl, alignItems: "center" },
  empty: { ...typography.body, textAlign: "center", paddingVertical: spacing.xxl },
});
