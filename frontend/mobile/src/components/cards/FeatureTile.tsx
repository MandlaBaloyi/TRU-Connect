import React from "react";
import { Pressable, StyleSheet } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { AppCard } from "./AppCard";
import { spacing } from "@/theme/spacing";

interface FeatureTileProps {
  label: string;
  icon: React.ReactNode;
  onPress?: () => void;
}

/**
 * Compact tappable tile used for dashboard Quick Actions (Upload Receipts,
 * Add Supplier, Verify Information). Ref: master prompt "REUSABLE
 * COMPONENTS" (FeatureTile) and docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt
 * (Home Dashboard -- Quick Actions).
 */
export function FeatureTile({ label, icon, onPress }: FeatureTileProps) {
  const theme = useTheme();
  return (
    <Pressable onPress={onPress} style={styles.pressable}>
      <AppCard style={styles.tile}>
        {icon}
        <Text
          variant="bodyMedium"
          numberOfLines={2}
          style={{
            color: theme.colors.onSurface,
            marginTop: spacing.sm,
            textAlign: "center",
            lineHeight: 20,
            fontWeight: "500",
          }}
        >
          {label}
        </Text>
      </AppCard>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  pressable: { flex: 1 },
  tile: {
    alignItems: "center",
    justifyContent: "center",
    minHeight: 110,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.sm,
  },
});