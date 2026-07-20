import React from "react";
import { StyleSheet, View } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { ChevronLeft } from "lucide-react-native";
import { Pressable } from "react-native";
import { spacing } from "@/theme/spacing";

interface ScreenHeaderProps {
  title?: string;
  onBack?: () => void;
}

/**
 * Reusable in-screen header with an optional back button, used on wizard
 * steps and other stacked screens that need a consistent title/back
 * affordance without a full native navigation header.
 * Ref: master prompt component architecture (components/navigation/).
 */
export function ScreenHeader({ title, onBack }: ScreenHeaderProps) {
  const theme = useTheme();
  return (
    <View style={styles.row}>
      {onBack && (
        <Pressable onPress={onBack} hitSlop={12} style={styles.backButton}>
          <ChevronLeft size={24} color={theme.colors.onSurface} />
        </Pressable>
      )}
      {title && (
        <Text variant="titleMedium" style={{ fontWeight: "700" }}>
          {title}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: spacing.sm, marginBottom: spacing.md },
  backButton: { padding: spacing.xs },
});
