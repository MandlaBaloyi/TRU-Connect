import React from "react";
import { StyleSheet, View } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { AppCard } from "@/components/cards/AppCard";
import { spacing } from "@/theme/spacing";

interface AnalyticsCardProps {
  title: string;
  icon: React.ReactNode;
  status?: string;
}

/**
 * Placeholder analytics tile -- reserves visual space and a consistent
 * shape for Phase 3 algorithm output (Top Products, Revenue Trend,
 * Fastest Moving Stock, Customer Growth, Sales Trend, Delivery
 * Performance) without pretending the analysis already exists.
 * Ref: master prompt "Analytics" (Supplier) and "Dashboard Algorithms" --
 * "Dashboards must not simply display database values. They must
 * prepare for business algorithms."
 */
export function AnalyticsCard({ title, icon, status = "Coming soon" }: AnalyticsCardProps) {
  const theme = useTheme();
  return (
    <AppCard style={styles.card}>
      <View style={styles.iconWrap}>{icon}</View>
      <Text variant="bodyMedium" style={styles.title}>
        {title}
      </Text>
      <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
        {status}
      </Text>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { width: 160, marginRight: spacing.sm, minHeight: 110 },
  iconWrap: { marginBottom: spacing.xs },
  title: { fontWeight: "600" },
});
