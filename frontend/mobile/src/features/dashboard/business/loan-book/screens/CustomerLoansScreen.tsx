/**
 * CustomerLoansScreen — everything for one customer. Theme-aware.
 *
 * TWO ADDITIONS:
 *   1. "Record another sale" now passes this customer's id/name as route
 *      params, so RecordSaleScreen pre-fills "Who is buying?" instead of
 *      making the owner search again for someone they're already
 *      looking at (Doc 02 §1.2: minimum typing).
 *   2. "Delete customer" — needed once a Loan Book has hundreds of
 *      customers and some genuinely need cleaning up (duplicates, a
 *      business that closed). Soft-delete via ReasonPromptModal, never
 *      an immediate unrecoverable removal — see Trash screen.
 */

import React, { useMemo, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Trash2 } from "lucide-react-native";

import { useCustomer, useCustomerActions } from "../hooks";
import { formatCents } from "../services/loanMapper";
import {
  describePurchaseFrequency,
  describeRepaymentBehaviour,
} from "../algorithms/repaymentPredictor";
import { CustomerAvatar, InsightList, LoanCard, ReasonPromptModal } from "../components";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";

export default function CustomerLoansScreen() {
  const router = useRouter();
  const theme = useTheme();
  const { customerId } = useLocalSearchParams<{ customerId: string }>();
  const { customer, isLoading, isError, notFound, refetch } = useCustomer(customerId ?? "");
  const { deleteCustomer, isDeletingCustomer } = useCustomerActions();
  const [deleteModalVisible, setDeleteModalVisible] = useState(false);

  const insights = useMemo(() => {
    if (!customer) return [];
    const pairs = customer.entries.map((view) => ({ entry: view.entry, payments: view.payments }));
    const behaviour = describeRepaymentBehaviour(pairs);
    const frequency = describePurchaseFrequency(customer.entries.map((view) => view.entry));
    return frequency ? [...behaviour, frequency] : behaviour;
  }, [customer]);

  if (isLoading) {
    return (
      <ScreenContainer>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (notFound || isError || !customer) {
    return (
      <ScreenContainer>
        <ErrorState
          message={
            notFound
              ? "Customer not found. It may have been removed."
              : "Could not load this customer. Check your connection and try again."
          }
          onRetry={notFound ? undefined : refetch}
        />
      </ScreenContainer>
    );
  }

  const handleRecordAnotherSale = () => {
    // Pre-fill the customer — see file docstring. encodeURIComponent
    // matters here: names can contain spaces/apostrophes that would
    // otherwise corrupt the query string.
    router.push(
      `/business/loan-book/record-sale?customerId=${customer.customer.id}&customerName=${encodeURIComponent(
        customer.customer.name
      )}`
    );
  };

  const handleConfirmDelete = async (reason?: string) => {
    setDeleteModalVisible(false);
    await deleteCustomer({ customerId: customer.customer.id, reason });
    router.back();
  };

  return (
    <ScreenContainer>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <CustomerAvatar name={customer.customer.name} seed={customer.customer.id} size={64} />
          <Text style={[styles.name, { color: theme.colors.onBackground }]}>{customer.customer.name}</Text>
          {customer.customer.phone && (
            <Text style={[styles.phone, { color: theme.colors.onSurfaceVariant }]}>
              {customer.customer.phone}
            </Text>
          )}
        </View>

        <View style={styles.totalBlock}>
          <Text style={[styles.totalLabel, { color: theme.colors.onSurfaceVariant }]}>Owes you</Text>
          <Text
            style={[
              styles.total,
              { color: customer.hasOverdue ? theme.colors.error : theme.colors.onBackground },
            ]}
          >
            {formatCents(customer.totalOutstanding)}
          </Text>
          <Text style={[styles.totalMeta, { color: theme.colors.onSurfaceVariant }]}>
            {customer.openEntryCount === 0
              ? "All settled"
              : customer.openEntryCount === 1
                ? "1 unpaid purchase"
                : `${customer.openEntryCount} unpaid purchases`}
          </Text>
        </View>

        <InsightList insights={insights} />

        <Pressable
          style={({ pressed }) => [
            styles.primaryButton,
            { backgroundColor: theme.colors.primary },
            pressed && styles.pressed,
          ]}
          onPress={handleRecordAnotherSale}
          accessibilityRole="button"
          accessibilityLabel={`Record another credit sale for ${customer.customer.name}`}
        >
          <Text style={[styles.primaryButtonText, { color: theme.colors.onPrimary }]}>
            Record another sale
          </Text>
        </Pressable>

        <View style={styles.listBlock}>
          <Text style={[styles.listTitle, { color: theme.colors.onSurface }]}>All purchases</Text>
          {customer.entries.map((view, index) => (
            <React.Fragment key={view.entry.id}>
              {index > 0 && (
                <View style={[styles.rowSeparator, { backgroundColor: theme.colors.outline }]} />
              )}
              <LoanCard
                view={view}
                customerName={customer.customer.name}
                onPress={() => router.push(`/business/loan-book/${view.entry.id}`)}
              />
            </React.Fragment>
          ))}
        </View>

        <Pressable
          onPress={() => setDeleteModalVisible(true)}
          disabled={isDeletingCustomer}
          style={styles.deleteButton}
          accessibilityRole="button"
          accessibilityLabel={`Delete ${customer.customer.name}`}
        >
          <Trash2 size={16} color={theme.colors.error} strokeWidth={2} />
          <Text style={[styles.deleteText, { color: theme.colors.error }]}>Delete customer</Text>
        </Pressable>
      </ScrollView>

      <ReasonPromptModal
        visible={deleteModalVisible}
        title="Delete this customer?"
        description={`${customer.customer.name} and their ${customer.entries.length === 1 ? "purchase" : "purchases"} move to Trash. Restorable for 7 days.`}
        confirmLabel="Delete"
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteModalVisible(false)}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.lg },
  centre: { paddingVertical: spacing.xxl, alignItems: "center" },
  header: { alignItems: "center", gap: spacing.xs },
  name: { ...typography.h1, textAlign: "center" },
  phone: { ...typography.body },
  totalBlock: { alignItems: "center", gap: spacing.xs },
  totalLabel: { ...typography.bodySmall },
  total: { ...typography.display },
  totalMeta: { ...typography.bodySmall },
  primaryButton: { minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radius.md },
  primaryButtonText: { ...typography.h2 },
  pressed: { opacity: 0.8 },
  listBlock: { gap: 0 },
  rowSeparator: { height: StyleSheet.hairlineWidth },
  listTitle: { ...typography.h2 },
  deleteButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.xs,
    minHeight: 44,
    marginTop: spacing.sm,
  },
  deleteText: { ...typography.body },
});
