import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Package, UserPlus } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { formatRelativeTime } from "@/utils/formatRelativeTime";
import type { Notification } from "../types";

interface Props {
  notification: Notification;
  onPress: () => void;
}

/**
 * One row -- unread state is genuinely visible (a filled dot, bolder
 * text, a faint tinted background), not just implied by a read/unread
 * boolean sitting invisibly in the data. Real category icon per row,
 * matching how modern notification feeds (and the two-tab split
 * itself) treat "what kind of thing is this" as worth showing at a
 * glance, not just the text alone.
 */
export function NotificationRow({ notification, onPress }: Props) {
  const theme = useTheme();
  const Icon = notification.category === "STOCK_ORDER" ? Package : UserPlus;

  return (
    <Pressable
      onPress={onPress}
      style={[
        styles.row,
        { borderColor: theme.colors.outlineVariant },
        !notification.isRead && { backgroundColor: theme.colors.primaryContainer },
      ]}
      accessibilityRole="button"
      accessibilityLabel={notification.body}
    >
      <View style={[styles.iconWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
        <Icon size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
      </View>

      <View style={styles.textColumn}>
        <View style={styles.titleRow}>
          <Text
            style={[
              styles.title,
              { color: theme.colors.onSurface },
              !notification.isRead && styles.titleUnread,
            ]}
            numberOfLines={1}
          >
            {notification.title}
          </Text>
          <Text style={[styles.time, { color: theme.colors.onSurfaceVariant }]}>
            {formatRelativeTime(notification.createdAt)}
          </Text>
        </View>
        <Text
          style={[styles.body, { color: theme.colors.onSurfaceVariant }]}
          numberOfLines={2}
        >
          {notification.body}
        </Text>
      </View>

      {!notification.isRead && <View style={[styles.unreadDot, { backgroundColor: theme.colors.primary }]} />}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: radius.pill,
    alignItems: "center",
    justifyContent: "center",
  },
  textColumn: { flex: 1, gap: 2 },
  titleRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: spacing.sm },
  title: { ...typography.body, fontWeight: "600", flexShrink: 1 },
  titleUnread: { fontWeight: "700" },
  time: { ...typography.caption },
  body: { ...typography.bodySmall, lineHeight: 18 },
  unreadDot: { width: 8, height: 8, borderRadius: 4, marginTop: 6 },
});
