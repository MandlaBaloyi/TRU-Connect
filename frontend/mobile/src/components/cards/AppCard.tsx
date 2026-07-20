import React from "react";
import { StyleSheet, View, ViewStyle } from "react-native";
import { useTheme } from "react-native-paper";
import { radius, spacing } from "@/theme/spacing";

interface AppCardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  selected?: boolean;
}

/**
 * Shared card shell: rounded corners, soft shadow, consistent padding.
 * Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 7 (Cards).
 */
export function AppCard({ children, style, selected }: AppCardProps) {
  const theme = useTheme();
  return (
    <View
      style={[
        styles.card,
        {
          backgroundColor: theme.colors.surface,
          borderColor: selected ? theme.colors.primary : "transparent",
        },
        style,
      ]}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: radius.lg,
    padding: spacing.lg,
    borderWidth: 2,
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 3,
  },
});
