import React from "react";
import { View, StyleSheet } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { spacing } from "@/theme/spacing";

interface EmptyStateProps {
  icon?: React.ReactNode;
  message: string;
  actionLabel?: string;
  onActionPress?: () => void;
}

/**  "REUSABLE COMPONENTS" (EmptyState) */
export function EmptyState({ icon, message, actionLabel, onActionPress }: EmptyStateProps) {
  const theme = useTheme();
  return (
    <View style={styles.container}>
      {icon}
      <Text style={{ color: theme.colors.onSurfaceVariant, textAlign: "center", marginTop: spacing.sm }}>
        {message}
      </Text>
      {actionLabel && onActionPress && (
        <PrimaryButton onPress={onActionPress} style={{ marginTop: spacing.md }}>
          {actionLabel}
        </PrimaryButton>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center", padding: spacing.xl },
});
