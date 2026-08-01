import React from "react";
import { View, StyleSheet } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { spacing } from "@/theme/spacing";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

/**  "REUSABLE COMPONENTS" (ErrorState) */
export function ErrorState({ message = "Something went wrong. Please try again.", onRetry }: ErrorStateProps) {
  const theme = useTheme();
  return (
    <View style={styles.container}>
      <Text style={{ color: theme.colors.error, textAlign: "center" }}>{message}</Text>
      {onRetry && (
        <PrimaryButton onPress={onRetry} style={{ marginTop: spacing.md }}>
          Try Again
        </PrimaryButton>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center", padding: spacing.xl },
});
