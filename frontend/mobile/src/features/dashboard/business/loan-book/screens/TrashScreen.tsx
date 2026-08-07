/**
 * TrashScreen — deleted customers and entries, restorable within the
 * retention window (algorithms/trashRetention.ts).
 *
 * DELIBERATELY NOT ONE ROW PER ENTRY. While a customer sits in Trash,
 * every one of their purchases is already summarised by that customer's
 * single row ("All settled" / "3 unpaid purchases · R510.00") — showing
 * each purchase again underneath would just repeat the same information.
 * An entry only earns its OWN row here when it was deleted independently
 * while its customer stayed active — and that row shows the customer's
 * name, since it has no other context otherwise.
 *
 * HONEST LIMITATION shown directly on screen, not hidden: this data
 * resets on app reload, same as the rest of Loan Book in this phase.
 */

import React from "react";
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { useTrash } from "../hooks";
import { formatCents } from "../services/loanMapper";
import { formatTrashCountdown } from "../algorithms/trashRetention";
import { CustomerAvatar } from "../components";
import { RestoreRow } from "../components/RestoreRow";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";

type TrashRow =
  | {
      kind: "customer";
      id: string;
      name: string;
      deletedAt: string;
      reason?: string;
      openEntryCount: number;
      totalEntryCount: number;
      totalOutstanding: number;
    }
  | {
      kind: "entry";
      id: string;
      customerName: string;
      label: string;
      amount: number;
      deletedAt: string;
      reason?: string;
    };

/** Same wording CustomerLoansScreen already uses for this exact
 *  concept — a deleted customer's row should read identically to how
 *  it read before it was deleted, not invent new phrasing. */
function purchaseSummary(openEntryCount: number, totalEntryCount: number): string {
  if (totalEntryCount === 0) return "No purchases";
  if (openEntryCount === 0) return "All settled";
  return openEntryCount === 1 ? "1 unpaid purchase" : `${openEntryCount} unpaid purchases`;
}

export default function TrashScreen() {
  const theme = useTheme();
  const {
    deletedCustomers,
    deletedEntries,
    isLoading,
    isError,
    isEmpty,
    refetch,
    restoreCustomer,
    isRestoringCustomer,
    restoreEntry,
    isRestoringEntry,
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
        <ErrorState message="Could not load Trash. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const rows: TrashRow[] = [
    ...deletedCustomers.map(
      (summary): TrashRow => ({
        kind: "customer",
        id: summary.customer.id,
        name: summary.customer.name,
        deletedAt: summary.customer.deletedAt!,
        reason: summary.customer.deletionReason,
        openEntryCount: summary.openEntryCount,
        totalEntryCount: summary.totalEntryCount,
        totalOutstanding: summary.totalOutstanding,
      })
    ),
    ...deletedEntries.map(
      ({ view, customerName }): TrashRow => ({
        kind: "entry",
        id: view.entry.id,
        customerName,
        label: view.entry.description ?? "Credit sale",
        amount: view.entry.originalAmount,
        deletedAt: view.entry.deletedAt!,
        reason: view.entry.deletionReason,
      })
    ),
  ].sort((a, b) => new Date(b.deletedAt).getTime() - new Date(a.deletedAt).getTime());

  return (
    <ScreenContainer>
      <FlatList
        data={rows}
        keyExtractor={(row) => `${row.kind}-${row.id}`}
        contentContainerStyle={styles.content}
        ListHeaderComponent={
          <Text style={[styles.notice, { color: theme.colors.onSurfaceVariant }]}>
               Deleted items are kept for 7 days before they are permanently deleted.
          </Text>
        }
        ItemSeparatorComponent={() => (
          <View style={[styles.separator, { backgroundColor: theme.colors.outline }]} />
        )}
        renderItem={({ item }) =>
          item.kind === "customer" ? (
            <RestoreRow
              icon={<CustomerAvatar name={item.name} seed={item.id} size={40} />}
              title={item.name}
              subtitle={
                item.reason
                  ? `${purchaseSummary(item.openEntryCount, item.totalEntryCount)} · ${formatCents(item.totalOutstanding)} · ${item.reason}`
                  : `${purchaseSummary(item.openEntryCount, item.totalEntryCount)} · ${formatCents(item.totalOutstanding)}`
              }
              countdown={formatTrashCountdown(item.deletedAt)}
              onRestore={() => restoreCustomer(item.id)}
              isRestoring={isRestoringCustomer}
            />
          ) : (
            <RestoreRow
              title={item.customerName}
              subtitle={
                item.reason
                  ? `${item.label} · ${formatCents(item.amount)} · ${item.reason}`
                  : `${item.label} · ${formatCents(item.amount)}`
              }
              countdown={formatTrashCountdown(item.deletedAt)}
              onRestore={() => restoreEntry(item.id)}
              isRestoring={isRestoringEntry}
            />
          )
        }
        ListEmptyComponent={
          isEmpty ? (
            <View style={styles.emptyWrapper}>
              <Text style={[styles.emptyTitle, { color: theme.colors.onBackground }]}>
                Trash is empty
              </Text>
              <Text style={[styles.emptyBody, { color: theme.colors.onSurfaceVariant }]}>
                Deleted customers and entries can be restored for 7 days before they are permanently deleted.
              </Text>
            </View>
          ) : null
        }
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.sm },
  centre: { paddingVertical: spacing.xxl, alignItems: "center" },
  notice: { ...typography.bodySmall, marginBottom: spacing.sm },
  separator: { height: StyleSheet.hairlineWidth },
  emptyWrapper: { alignItems: "center", paddingVertical: spacing.xxl, gap: spacing.sm },
  emptyTitle: { ...typography.h2 },
  emptyBody: { ...typography.body, textAlign: "center" },
});
