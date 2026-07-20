import React, { useEffect } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { Text, useTheme } from "react-native-paper";
import Animated, { useSharedValue, useAnimatedStyle, withTiming } from "react-native-reanimated";
import { AppCard } from "./AppCard";
import { spacing } from "@/theme/spacing";

interface RoleCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  selected: boolean;
  onPress: () => void;
}

/**
 * Role Selection card (Business Owner / Supplier), with a subtle Reanimated
 * scale animation on selection. Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt
 * (Role Selection screen) and master prompt "ANIMATIONS" (subtle, fast,
 * professional).
 */
export function RoleCard({ title, description, icon, selected, onPress }: RoleCardProps) {
  const theme = useTheme();
  const scale = useSharedValue(1);

  useEffect(() => {
    scale.value = withTiming(selected ? 1.02 : 1, { duration: 150 });
  }, [selected, scale]);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return (
    <Pressable onPress={onPress} accessibilityRole="button" accessibilityState={{ selected }}>
      <Animated.View style={animatedStyle}>
        <AppCard selected={selected} style={styles.card}>
          <View style={styles.iconWrap}>{icon}</View>
          <Text variant="titleMedium" style={{ fontWeight: "700", marginTop: spacing.sm }}>
            {title}
          </Text>
          <Text
            variant="bodyMedium"
            style={{ color: theme.colors.onSurfaceVariant, marginTop: spacing.xs }}
          >
            {description}
          </Text>
        </AppCard>
      </Animated.View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { marginBottom: spacing.md },
  iconWrap: { width: 48, height: 48, justifyContent: "center", alignItems: "flex-start" },
});
