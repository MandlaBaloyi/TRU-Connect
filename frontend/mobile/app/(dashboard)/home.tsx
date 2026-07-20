import React from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { Text, Avatar } from "react-native-paper";
import { Receipt, UserPlus, ShieldCheck } from "lucide-react-native";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppCard } from "@/components/cards/AppCard";
import { FeatureTile } from "@/components/cards/FeatureTile";
import { EmptyState } from "@/components/feedback/EmptyState";
import { ErrorState } from "@/components/feedback/ErrorState";
import { useBusinessDashboard } from "@/features/dashboard/hooks/useBusinessDashboard";
import { spacing } from "@/theme/spacing";

/**
 * Home Dashboard (foundation for Phase 1).
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Business Dashboard)
 * and docs/07_DATA_AND_TRUST_ENGINE.txt (Business Trust Score /
 * business_health_scores).
 *
 * Full dashboard composition (Today's Orders, Nearby Suppliers,
 * Recommended Products, Recent Activity Timeline) is scoped for the next
 * phase of screens; this establishes the route, data-fetching pattern, and
 * Quick Actions used by later phases.
 */
export default function HomeDashboard() {
  const { data, isLoading, isError, refetch } = useBusinessDashboard();

  if (isError) return <ErrorState onRetry={() => refetch()} />;

  return (
    <ScreenContainer>
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <View>
            <Text variant="bodyMedium" style={{ opacity: 0.6 }}>
              Welcome back,
            </Text>
            <Text variant="headlineSmall" style={{ fontWeight: "700" }}>
              {data?.businessName ?? "Your Business"}
            </Text>
          </View>
          <Avatar.Text size={44} label="TC" />
        </View>

        <AppCard style={{ marginTop: spacing.lg }}>
          <Text variant="bodySmall" style={{ opacity: 0.6 }}>
            Business Trust Score
          </Text>
          <Text variant="displaySmall" style={{ fontWeight: "700", marginTop: spacing.xs }}>
            {isLoading ? "..." : data?.trustScore ?? "--"}
          </Text>
          <Text variant="bodySmall" style={{ opacity: 0.6, marginTop: spacing.xs }}>
            Builds automatically as you trade -- see
            docs/07_DATA_AND_TRUST_ENGINE.txt
          </Text>
        </AppCard>

        <View style={styles.row}>
          <AppCard style={styles.halfCard}>
            <Text style={{ opacity: 0.6 }}>Today's Sales</Text>
            <Text variant="titleLarge" style={{ fontWeight: "700" }}>
              {isLoading ? "..." : data?.todaySales ?? "R0"}
            </Text>
          </AppCard>
          <AppCard style={styles.halfCard}>
            <Text style={{ opacity: 0.6 }}>Trading Activity</Text>
            <Text variant="titleLarge" style={{ fontWeight: "700" }}>
              {isLoading ? "..." : data?.tradingActivityCount ?? 0}
            </Text>
          </AppCard>
        </View>

        <Text variant="titleMedium" style={{ fontWeight: "700", marginTop: spacing.lg }}>
          Quick Actions
        </Text>
        <View style={[styles.row, { gap: spacing.sm }]}>
          <FeatureTile label="Upload Receipts" icon={<Receipt size={22} />} />
          <FeatureTile label="Add Supplier" icon={<UserPlus size={22} />} />
          <FeatureTile label="Verify Information" icon={<ShieldCheck size={22} />} />
        </View>

        <Text variant="titleMedium" style={{ fontWeight: "700", marginTop: spacing.lg }}>
          Recent Activity
        </Text>
        <View style={{ marginTop: spacing.sm, marginBottom: spacing.xl }}>
          <EmptyState message="No activity yet. Once you start trading, your activity timeline appears here." />
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: spacing.lg,
  },
  row: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.md },
  halfCard: { flex: 1 },
});
