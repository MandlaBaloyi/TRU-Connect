/**
 * LoanHistoryScreen — Transaction History. A bank-statement view of the
 * Loan Book: who bought, who paid, how much, when — nothing else.
 *
 * SCOPE: filtered to just SALE_CREATED / PAYMENT_RECORDED /
 * PAYMENT_REMOVED via filterTransactionEvents(). The underlying event
 * log (types.ts's LoanHistoryEvent) still records everything —
 * deletions, restores, receipt views/shares — for the "complete lending
 * history" data-scaling goal, but this screen's whole premise is "what
 * money moved", the same way a real bank statement never mixes in "card
 * PIN changed" alongside your transactions.
 *
 * FLAT ROWS, NO CARDS. Matches the same flat-list treatment applied
 * throughout this feature (CustomerCard/LoanCard/RestoreRow) — a day's
 * transactions sit under a plain text day label, separated from each
 * other and from the next day by a hairline, not wrapped in a bordered
 * container.
 */

import React, { useMemo } from "react";
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { useLoanBook, useLoanHistory } from "../hooks";
import { filterTransactionEvents, groupHistoryByDay, type HistoryDayGroup } from "../services/loanHistory";
import { TransactionRow } from "../components/TransactionRow";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";

export default function LoanHistoryScreen() {
  const theme = useTheme();
  const { events, isLoading, isError, refetch } = useLoanHistory();
  const { customers } = useLoanBook();

  const customerNames = useMemo(() => {
    const map = new Map<string, string>();
    customers.forEach((view) => map.set(view.customer.id, view.customer.name));
    return map;
  }, [customers]);

  const transactionEvents = useMemo(() => filterTransactionEvents(events), [events]);
  const groups = useMemo(() => groupHistoryByDay(transactionEvents), [transactionEvents]);
  const isEmpty = !isLoading && transactionEvents.length === 0;

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState
          message="Could not load the transaction history. Check your connection and try again."
          onRetry={refetch}
        />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader>
      <FlatList<HistoryDayGroup>
        data={groups}
        keyExtractor={(group, index) => `${group.label}-${index}`}
        contentContainerStyle={styles.content}
        renderItem={({ item }) => (
          <View style={styles.dayGroup}>
            <Text style={[styles.dayLabel, { color: theme.colors.onSurfaceVariant }]}>{item.label}</Text>
            {item.events.map((event, index) => (
              <React.Fragment key={event.id}>
                {index > 0 && (
                  <View style={[styles.rowSeparator, { backgroundColor: theme.colors.outline }]} />
                )}
                <TransactionRow event={event} customerName={customerNames.get(event.customerId) ?? "Unknown customer"} />
              </React.Fragment>
            ))}
          </View>
        )}
        ItemSeparatorComponent={() => (
          <View style={[styles.daySeparator, { backgroundColor: theme.colors.outline }]} />
        )}
        ListEmptyComponent={
          isEmpty ? (
            <View style={styles.emptyWrapper}>
              <Text style={[styles.emptyTitle, { color: theme.colors.onBackground }]}>
                No transactions yet
              </Text>
              <Text style={[styles.emptyBody, { color: theme.colors.onSurfaceVariant }]}>
                Every loan and payment will appear here, like a statement.
              </Text>
            </View>
          ) : null
        }
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl },
  centre: { paddingVertical: spacing.xxl, alignItems: "center" },
  dayGroup: { gap: 0 },
  dayLabel: { ...typography.bodySmall, fontWeight: "600", marginBottom: spacing.xs },
  rowSeparator: { height: StyleSheet.hairlineWidth },
  daySeparator: { height: StyleSheet.hairlineWidth, marginVertical: spacing.md },
  emptyWrapper: { alignItems: "center", paddingVertical: spacing.xxl, gap: spacing.sm },
  emptyTitle: { ...typography.h2 },
  emptyBody: { ...typography.body, textAlign: "center" },
});
