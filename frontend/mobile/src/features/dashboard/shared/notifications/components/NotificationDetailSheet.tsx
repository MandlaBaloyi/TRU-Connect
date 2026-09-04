import React from "react";
import { Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Package, UserPlus, X } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { Notification } from "../types";

interface Props {
  notification: Notification | null;
  onClose: () => void;
}

/**
 * THE HONEST, "FOR NOW" VERSION -- shows the notification's own full,
 * unclipped message and nothing more. Deliberately NOT the real order
 * detail (no items, no payment breakdown, no Approve/Decline) --
 * confirmed directly: that's separate, future, core supplier
 * functionality this notification will eventually link INTO, not
 * something the notifications feature owns or should attempt to
 * half-build itself. This is genuinely the notification's own whole
 * job finishing, not a placeholder pretending to be more than it is.
 */
export function NotificationDetailSheet({ notification, onClose }: Props) {
  const theme = useTheme();
  if (!notification) return null;

  const Icon = notification.category === "STOCK_ORDER" ? Package : UserPlus;
  const fullDate = new Date(notification.createdAt).toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <Modal visible transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable style={[styles.card, { backgroundColor: theme.colors.background }]} onPress={() => {}}>
          <View style={styles.header}>
            <View style={[styles.iconWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
              <Icon size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
            </View>
            <Pressable onPress={onClose} hitSlop={10} accessibilityRole="button" accessibilityLabel="Close">
              <X size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
            </Pressable>
          </View>

          <Text style={[styles.title, { color: theme.colors.onSurface }]}>{notification.title}</Text>
          <Text style={[styles.body, { color: theme.colors.onSurface }]}>{notification.body}</Text>
          <Text style={[styles.timestamp, { color: theme.colors.onSurfaceVariant }]}>{fullDate}</Text>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.4)", alignItems: "center", justifyContent: "center", padding: spacing.lg },
  card: { width: "100%", maxWidth: 360, borderRadius: radius.lg, padding: spacing.lg },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: spacing.md },
  iconWrap: { width: 36, height: 36, borderRadius: radius.pill, alignItems: "center", justifyContent: "center" },
  title: { ...typography.h2, fontWeight: "700", marginBottom: spacing.sm },
  body: { ...typography.body, lineHeight: 22, marginBottom: spacing.md },
  timestamp: { ...typography.bodySmall },
});
