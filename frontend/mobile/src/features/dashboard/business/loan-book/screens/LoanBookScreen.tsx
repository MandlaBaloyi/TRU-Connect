/**
 * LoanBookScreen — CUSTOMER-FIRST main list.
 *
 * REDESIGNED: previously listed individual LoanEntryView rows, which
 * meant the same customer with two purchases showed up as two separate
 * cards with two separate small balances — leaving the business owner
 * to do the addition themselves to answer "how much does this person
 * actually owe me?" That's the wrong abstraction: a shop owner thinks
 * "Mandla owes me R510", the same way a banking app shows one account
 * balance, not a card per debit transaction.
 *
 * The underlying data is UNCHANGED — every purchase is still its own
 * entry, with its own receipt, payment history, and audit trail (see
 * CustomerLoansScreen, reached by tapping a row here, for the individual
 * purchases). Only this list's abstraction changed, from entries to
 * customer accounts.
 */

import React from "react";
import { ActivityIndicator, FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Trash2, History } from "lucide-react-native";

import { useLoanBook } from "../hooks";

import * as loanBookApiModule from "../api/loanBookApi";

console.log("=== LOAN BOOK DEBUG ===");
console.log("EXPO_PUBLIC_USE_MOCK_API raw:", JSON.stringify(process.env.EXPO_PUBLIC_USE_MOCK_API));
console.log("typeof:", typeof process.env.EXPO_PUBLIC_USE_MOCK_API);
console.log("Loaded module keys:", Object.keys(loanBookApiModule));


import { useCustomerFilters } from "../hooks/useCustomerFilters";
import { applyCustomerFilters } from "../services/customerFilters";
import type { CustomerView } from "../types";
import {
  CustomerCard,
  CustomerFilterBar,
  EmptyLoanBook,
  LoanSearchBar,
  OutstandingAmountCard,
} from "../components";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";



export default function LoanBookScreen() {
  const router = useRouter();
  const theme = useTheme();
  const filterState = useCustomerFilters();
  const { summary, customers, isLoading, isRefreshing, isError, refetch } = useLoanBook();

  const filteredCustomers = applyCustomerFilters(customers, filterState.filters);
  const isEmpty = !isLoading && customers.length === 0;
  const isFilteredEmpty = !isLoading && customers.length > 0 && filteredCustomers.length === 0;

  const goToRecordSale = () => router.push("/business/loan-book/record-sale");
  const goToCustomer = (customerId: string) =>
    router.push(`/business/loan-book/customer/${customerId}`);

  if (isError) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState
          message="Could not load your loan book. Check your connection and try again."
          onRetry={refetch}
        />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader>
      <FlatList<CustomerView>
        data={filteredCustomers}
        keyExtractor={(item) => item.customer.id}
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={refetch}
            tintColor={theme.colors.primary}
          />
        }
        ListHeaderComponent={
          <View style={styles.header}>
            {summary && (
              <OutstandingAmountCard
                summary={summary}
                onRecordSale={goToRecordSale}
                onViewLoanBook={undefined}
              />
            )}
            <LoanSearchBar
              value={filterState.searchTerm}
              onChangeText={filterState.setSearchTerm}
              onClear={() => filterState.setSearchTerm("")}
            />
            <CustomerFilterBar
              status={filterState.status}
              onStatusChange={filterState.setStatus}
              sortBy={filterState.sortBy}
              onSortChange={filterState.setSortBy}
            />
            <View style={styles.countRow}>
              {filteredCustomers.length > 0 && (
                <Text style={[styles.count, { color: theme.colors.onSurfaceVariant }]}>
                  {filteredCustomers.length === 1 ? "1 customer" : `${filteredCustomers.length} customers`}
                </Text>
              )}
              <View style={styles.utilityLinks}>
                <Pressable
                  onPress={() => router.push("/business/loan-book/history")}
                  style={styles.utilityLink}
                  accessibilityRole="button"
                  accessibilityLabel="View activity history"
                  hitSlop={8}
                >
                  <History size={14} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
                  <Text style={[styles.utilityLinkText, { color: theme.colors.onSurfaceVariant }]}>
                    History
                  </Text>
                </Pressable>
                <Pressable
                  onPress={() => router.push("/business/loan-book/trash")}
                  style={styles.utilityLink}
                  accessibilityRole="button"
                  accessibilityLabel="View Trash"
                  hitSlop={8}
                >
                  <Trash2 size={14} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
                  <Text style={[styles.utilityLinkText, { color: theme.colors.onSurfaceVariant }]}>
                    Trash
                  </Text>
                </Pressable>
              </View>
            </View>
          </View>
        }
        renderItem={({ item }) => (
          <CustomerCard view={item} onPress={() => goToCustomer(item.customer.id)} />
        )}
        ItemSeparatorComponent={() => (
          <View style={[styles.separator, { backgroundColor: theme.colors.outline }]} />
        )}
        ListEmptyComponent={
          isLoading ? (
            <View style={styles.loading}>
              <ActivityIndicator color={theme.colors.primary} />
            </View>
          ) : isFilteredEmpty ? (
            <EmptyLoanBook variant="NO_RESULTS" onClearFilters={filterState.clear} />
          ) : isEmpty ? (
            <EmptyLoanBook variant="FIRST_RUN" onRecordSale={goToRecordSale} />
          ) : null
        }
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    paddingBottom: spacing.xxl,
    gap: spacing.sm,
  },
  header: { gap: spacing.md, marginBottom: spacing.sm },
  countRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  count: { ...typography.bodySmall },
  utilityLinks: { flexDirection: "row", gap: spacing.md },
  utilityLink: { flexDirection: "row", alignItems: "center", gap: 4, minHeight: 32, paddingHorizontal: spacing.xs },
  utilityLinkText: { ...typography.bodySmall, fontWeight: "600" },
  separator: { height: StyleSheet.hairlineWidth },
  loading: { paddingVertical: spacing.xxl, alignItems: "center" },
});
