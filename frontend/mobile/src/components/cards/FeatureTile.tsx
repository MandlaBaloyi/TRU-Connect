import React from "react";
import {
  Pressable,
  StyleSheet,
  ViewStyle,
} from "react-native";
import { Text, useTheme } from "react-native-paper";
import { AppCard } from "./AppCard";
import { spacing } from "@/theme/spacing";

interface FeatureTileProps {
  label: string;
  icon: React.ReactNode;
  onPress?: () => void;
  style?: ViewStyle;
}

/**
 * Dashboard Feature Tile.
 * The ENTIRE card is tappable.
 */
export function FeatureTile({
  label,
  icon,
  onPress,
  style,
}: FeatureTileProps) {
  const theme = useTheme();

  return (
    <Pressable
      onPress={onPress}
      hitSlop={8}
      pressRetentionOffset={20}
      android_ripple={{
        color: "rgba(0,0,0,0.08)",
      }}
      style={({ pressed }) => [
        style,               // sizing from parent (e.g. width: '31%')
        pressed && styles.pressed,
      ]}
    >
      <AppCard style={styles.tile}>
        {icon}

        <Text
          variant="bodyMedium"
          numberOfLines={2}
          style={[
            styles.label,
            {
              color: theme.colors.onSurface,
            },
          ]}
        >
          {label}
        </Text>
      </AppCard>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  pressed: {
    opacity: 0.85,
  },

  tile: {
    alignItems: "center",
    justifyContent: "center",

    minHeight: 96,          // was 120 — now more compact

    paddingVertical: spacing.sm,   // was spacing.md
    paddingHorizontal: spacing.sm,
  },

  label: {
    marginTop: spacing.xs,  // tighter spacing above label
    textAlign: "center",
    lineHeight: 20,
    fontWeight: "500",
  },
});