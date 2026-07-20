import React from "react";
import { View, StyleSheet, Modal } from "react-native";
import { ActivityIndicator, Text, useTheme } from "react-native-paper";
import { spacing } from "@/theme/spacing";

interface LoadingOverlayProps {
  visible: boolean;
  label?: string;
}

/**
 * Full-screen semi-transparent overlay with a spinner, used for blocking
 * async actions (e.g. submitting the Business Profile wizard) without
 * navigating away from the current screen.
 * Ref: master prompt "REUSABLE COMPONENTS" (LoadingOverlay) and
 * docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 2.3 (Loading States).
 */
export function LoadingOverlay({ visible, label = "Loading..." }: LoadingOverlayProps) {
  const theme = useTheme();
  if (!visible) return null;

  return (
    <Modal transparent visible={visible} animationType="fade">
      <View style={[styles.backdrop, { backgroundColor: "rgba(0,0,0,0.35)" }]}>
        <View style={[styles.card, { backgroundColor: theme.colors.surface }]}>
          <ActivityIndicator animating color={theme.colors.primary} size="large" />
          <Text style={{ marginTop: spacing.sm, color: theme.colors.onSurfaceVariant }}>{label}</Text>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, alignItems: "center", justifyContent: "center" },
  card: { borderRadius: 16, padding: spacing.xl, alignItems: "center", minWidth: 160 },
});
