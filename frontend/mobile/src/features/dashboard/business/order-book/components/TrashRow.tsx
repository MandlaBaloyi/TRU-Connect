import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { TrashReason } from "../types";
import { formatTrashCountdown } from "../algorithms/trashRetention";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";
import { radius } from "@/theme/spacing";

function reasonLabel(reason?: TrashReason): string {
  switch (reason) {
    case "AUTO_CLEAR_COMPLETED":
      return "Auto-cleared";
    case "MANUAL_CLEAR_COMPLETED":
      return "Cleared";
    case "MANUAL_DELETE":
    default:
      return "Deleted";
  }
}

interface Props {
  title: string;
  subtitle?: string;
  deletedAt: string;
  reason?: TrashReason;
  onRestore: () => void;
  isRestoring?: boolean;
}

export function TrashRow({ title, subtitle, deletedAt, reason, onRestore, isRestoring }: Props) {
  const theme = useTheme();
  return (
    <View style={styles.row}>
      <View style={styles.body}>
        <Text style={[styles.title, { color: theme.colors.onSurface }]} numberOfLines={1}>
          {title}
        </Text>
        <Text style={[styles.meta, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
          {reasonLabel(reason)} · {formatTrashCountdown(deletedAt)}
          {subtitle ? ` · ${subtitle}` : ""}
        </Text>
      </View>
      <Pressable
        onPress={onRestore}
        disabled={isRestoring}
        style={[styles.restoreButton, { borderColor: theme.colors.primary }]}
        accessibilityRole="button"
        accessibilityLabel={`Restore ${title}`}
      >
        <Text style={[styles.restoreText, { color: theme.colors.primary }]}>
          {isRestoring ? "Restoring…" : "Restore"}
        </Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: spacing.sm, paddingVertical: spacing.sm, minHeight: 44 },
  body: { flex: 1, gap: 2 },
  title: { ...typography.body, fontWeight: "600" },
  meta: { ...typography.bodySmall },
  restoreButton: { borderWidth: 1, borderRadius: radius.pill, paddingHorizontal: spacing.md, minHeight: 32, justifyContent: "center" },
  restoreText: { ...typography.bodySmall, fontWeight: "600" },
});
