/**
 * RestoreRow — one item in the Trash list (a deleted customer or a
 * deleted entry), with a countdown and a Restore button.
 */

import React from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Undo2 } from "lucide-react-native";

import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  icon?: React.ReactNode;
  title: string;
  subtitle: string;
  countdown: string;
  onRestore: () => void;
  isRestoring?: boolean;
}

export function RestoreRow({ icon, title, subtitle, countdown, onRestore, isRestoring }: Props) {
  const theme = useTheme();
  const isExpired = countdown === "Expired";

  return (
    <View
      style={styles.row}
    >
      {icon}
      <View style={styles.body}>
        <Text style={[styles.title, { color: theme.colors.onSurface }]} numberOfLines={1}>
          {title}
        </Text>
        <Text style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
          {subtitle}
        </Text>
        <Text
          style={[styles.countdown, { color: isExpired ? theme.colors.error : theme.colors.onSurfaceVariant }]}
        >
          {countdown}
        </Text>
      </View>
      <Pressable
        onPress={onRestore}
        disabled={isRestoring || isExpired}
        style={[styles.restoreButton, { borderColor: theme.colors.outline }]}
        accessibilityRole="button"
        accessibilityLabel={`Restore ${title}`}
      >
        {isRestoring ? (
          <ActivityIndicator size="small" color={theme.colors.primary} />
        ) : (
          <Undo2 size={16} color={theme.colors.primary} strokeWidth={2} />
        )}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    paddingVertical: spacing.sm,
    minHeight: 44,
  },
  body: { flex: 1, gap: 2 },
  title: { ...typography.body, fontWeight: "600" },
  subtitle: { ...typography.bodySmall },
  countdown: { ...typography.caption },
  restoreButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
});
