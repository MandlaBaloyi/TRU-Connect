import React from "react";
import { StyleSheet } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { AppCard } from "@/components/cards/AppCard";
import { spacing } from "@/theme/spacing";

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
}

/**
 * Generic single-metric card used in horizontal "snapshot" rows on both
 * dashboards (Today's Snapshot / Business Overview). Shared because the
 * shape (label + big value + optional icon) is identical across roles;
 * only the metrics shown differ.
 * Ref: master prompt "Today's Snapshot" and "Business Overview".
 */
export function StatCard({ label, value, icon }: StatCardProps) {
  const theme = useTheme();
  return (
    <AppCard style={styles.card}>
      {icon}
      <Text variant="bodySmall" style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>
        {label}
      </Text>
      <Text variant="titleLarge" style={styles.value}>
        {value}
      </Text>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { width: 148, marginRight: spacing.sm },
  label: { marginTop: spacing.xs },
  value: { fontWeight: "700", marginTop: 2 },
});
