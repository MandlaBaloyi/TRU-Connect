import React from "react";
import { View, StyleSheet } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { AppCard } from "@/components/cards/AppCard";
import { spacing } from "@/theme/spacing";

interface NotificationCardProps {
  icon: React.ReactNode;
  title: string;
  timestamp: string;
  isRead?: boolean;
}

/**
 * Shared notification-shaped row. Used both for real notifications (bell
 * icon dropdown/screen, future phase) and for the "Recent Activity
 * Timeline" on the Business dashboard (Receipt Uploaded, Order
 * Submitted, Supplier Added, Trust Score Increased, Verification
 * Approved) -- an activity entry is shaped identically to a
 * notification (icon + title + timestamp), so this one component covers
 * both rather than duplicating a near-identical "ActivityItem".
 */
export function NotificationCard({ icon, title, timestamp, isRead = true }: NotificationCardProps) {
  const theme = useTheme();
  return (
    <AppCard style={[styles.card, !isRead && { borderColor: theme.colors.primary }]}>
      <View style={styles.row}>
        <View style={[styles.iconWrap, { backgroundColor: theme.colors.primaryContainer }]}>{icon}</View>
        <View style={styles.textBlock}>
          <Text variant="bodyMedium" style={styles.title}>
            {title}
          </Text>
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
            {timestamp}
          </Text>
        </View>
      </View>
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { marginBottom: spacing.sm },
  row: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
  },
  textBlock: { flex: 1 },
  title: { fontWeight: "600" },
});
