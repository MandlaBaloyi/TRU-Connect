/**
 * LoanAnalyticsScreen — how the book is actually performing. Theme-aware.
 */

import React, { useMemo } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { useLoanBook } from "../hooks";
import { formatCents } from "../services/loanMapper";
import {
  AGING_BUCKET_LABELS,
  determineAgingBucket,
  type AgingBucket,
} from "../algorithms/agingCalculator";
import { CustomerCard, LoanSummaryCard } from "../components";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";

const BUCKET_ORDER: AgingBucket[] = [
  "CURRENT",
  "OVERDUE_RECENT",
  "OVERDUE_LONG",
  "OVERDUE_VERY_LONG",
];

export default function LoanAnalyticsScreen() {
  const router = useRouter();
  const theme = useTheme();
  const { summary, entries, customers, isLoading, isError, refetch } = useLoanBook();

  const buckets = useMemo(() => {
    const totals = new Map<AgingBucket, { count: number; amount: number }>();
    BUCKET_ORDER.forEach((bucket) => totals.set(bucket, { count: 0, amount: 0 }));

    entries
      .filter((view) => view.outstandingAmount > 0)
      .forEach((view) => {
        const bucket = determineAgingBucket(view.entry, view.payments);
        const current = totals.get(bucket)!;
        totals.set(bucket, {
          count: current.count + 1,
          amount: current.amount + view.outstandingAmount,
        });
      });

    return BUCKET_ORDER.map((bucket) => ({ bucket, ...totals.get(bucket)! }));
  }, [entries]);

  const largestBucketAmount = Math.max(1, ...buckets.map((b) => b.amount));
  const topDebtors = useMemo(
    () => customers.filter((c) => c.totalOutstanding > 0).slice(0, 5),
    [customers]
  );

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !summary) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Could not load your figures. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.statsGrid}>
          <LoanSummaryCard
            label="Customers"
            value={String(customers.length)}
            caption={`${entries.length} credit sales`}
          />
          <LoanSummaryCard
            label="Total outstanding"
            value={formatCents(summary.totalOutstanding)}
            caption={`${summary.customersOwingCount} still owing`}
          />
        </View>
        <View style={styles.statsGrid}>
          <LoanSummaryCard
            label="Overdue"
            value={formatCents(summary.overdueAmount)}
            caption={`${summary.overdueCount} entries`}
            tone={summary.overdueCount > 0 ? "ATTENTION" : "DEFAULT"}
          />
          <LoanSummaryCard
            label="Collected (30 days)"
            value={formatCents(summary.collectedLast30Days)}
            tone="POSITIVE"
          />
        </View>
        <View style={styles.statsGrid}>
          <LoanSummaryCard
            label="Overdue"
            value={formatCents(summary.overdueAmount)}
            caption={`${summary.overdueCount} entries`}
            tone={summary.overdueCount > 0 ? "ATTENTION" : "DEFAULT"}
          />
          <LoanSummaryCard
            label="Unpaid purchases"
            value={String(entries.filter((view) => view.outstandingAmount > 0).length)}
          />
        </View>

        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>
            How long money has been owed
          </Text>
          {buckets.map(({ bucket, count, amount }) => (
            <View key={bucket} style={styles.bucketRow}>
              <View style={styles.bucketHeader}>
                <Text style={[styles.bucketLabel, { color: theme.colors.onSurface }]}>
                  {AGING_BUCKET_LABELS[bucket]}
                </Text>
                <Text style={[styles.bucketAmount, { color: theme.colors.onSurface }]}>
                  {formatCents(amount)}
                </Text>
              </View>
              <View style={[styles.barTrack, { backgroundColor: theme.colors.surfaceVariant }]}>
                <View
                  style={[
                    styles.barFill,
                    {
                      width: `${Math.round((amount / largestBucketAmount) * 100)}%`,
                      backgroundColor: bucket === "CURRENT" ? theme.colors.secondary : theme.colors.error,
                    },
                  ]}
                />
              </View>
              <Text style={[styles.bucketCount, { color: theme.colors.onSurfaceVariant }]}>
                {count === 1 ? "1 entry" : `${count} entries`}
              </Text>
            </View>
          ))}
        </View>

        {topDebtors.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>Who owes the most</Text>
            {topDebtors.map((view) => (
              <CustomerCard
                key={view.customer.id}
                view={view}
                onPress={() =>
                  router.push(`/business/loan-book/customer/${view.customer.id}`)
                }
              />
            ))}
          </View>
        )}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.md },
  centre: { paddingVertical: spacing.xxl, alignItems: "center" },
  statsGrid: { flexDirection: "row", gap: spacing.sm },
  section: { gap: spacing.sm, marginTop: spacing.sm },
  sectionTitle: { ...typography.h2 },
  bucketRow: { gap: spacing.xs, marginBottom: spacing.sm },
  bucketHeader: { flexDirection: "row", justifyContent: "space-between", gap: spacing.sm },
  bucketLabel: { ...typography.body, flex: 1 },
  bucketAmount: { ...typography.body, fontWeight: "600" },
  barTrack: { height: 8, borderRadius: radius.pill, overflow: "hidden" },
  barFill: { height: 8, borderRadius: radius.pill },
  bucketCount: { ...typography.caption },
});
