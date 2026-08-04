/**
 * ReasonPromptModal — asks for a short reason before a destructive
 * action (deleting an entry or a customer), then confirms.
 *
 * Built as a real Modal + TextInput rather than the native Alert.prompt,
 * because Alert.prompt is iOS-only — Android has no equivalent, and this
 * app needs to work identically on both (Doc 02 targets Android as the
 * primary device).
 */

import React, { useState } from "react";
import { Modal, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useTheme } from "react-native-paper";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  visible: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  onConfirm: (reason?: string) => void;
  onCancel: () => void;
}

export function ReasonPromptModal({
  visible,
  title,
  description,
  confirmLabel = "Remove",
  onConfirm,
  onCancel,
}: Props) {
  const theme = useTheme();
  const [reason, setReason] = useState("");

  const handleConfirm = () => {
    onConfirm(reason.trim() || undefined);
    setReason("");
  };

  const handleCancel = () => {
    setReason("");
    onCancel();
  };

  return (
    <Modal visible={visible} animationType="fade" transparent onRequestClose={handleCancel}>
      <View style={styles.backdrop}>
        <View style={[styles.card, { backgroundColor: theme.colors.surface }]}>
          <Text style={[styles.title, { color: theme.colors.onSurface }]}>{title}</Text>
          <Text style={[styles.description, { color: theme.colors.onSurfaceVariant }]}>
            {description}
          </Text>

          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>
            Reason (optional)
          </Text>
          <TextInput
            value={reason}
            onChangeText={setReason}
            placeholder="e.g. Entered by mistake"
            placeholderTextColor={theme.colors.onSurfaceVariant}
            style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            accessibilityLabel="Reason for this action, optional"
          />

          <View style={styles.actions}>
            <Pressable
              onPress={handleCancel}
              style={[styles.action, { borderColor: theme.colors.outline }]}
              accessibilityRole="button"
              accessibilityLabel="Cancel"
            >
              <Text style={[styles.actionText, { color: theme.colors.onSurface }]}>Keep it</Text>
            </Pressable>
            <Pressable
              onPress={handleConfirm}
              style={[styles.action, { backgroundColor: theme.colors.error }]}
              accessibilityRole="button"
              accessibilityLabel={confirmLabel}
            >
              <Text style={[styles.actionText, { color: theme.colors.onError }]}>{confirmLabel}</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.lg,
  },
  card: { width: "100%", maxWidth: 400, borderRadius: radius.lg, padding: spacing.lg, gap: spacing.sm },
  title: { ...typography.h2 },
  description: { ...typography.body },
  label: { ...typography.bodySmall, marginTop: spacing.sm },
  input: { borderWidth: 1, borderRadius: radius.md, paddingHorizontal: spacing.md, minHeight: 48, ...typography.body },
  actions: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.md },
  action: {
    flex: 1,
    minHeight: 48,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: "transparent",
  },
  actionText: { ...typography.body, fontWeight: "600" },
});
