import React from "react";
import { View, StyleSheet, Pressable } from "react-native";
import { Text, Avatar, useTheme } from "react-native-paper";
import { spacing } from "@/theme/spacing";

interface HomeHeaderProps {
  greeting: string;
  name: string;
  avatarLabel: string;
  onProfilePress?: () => void;
}

/**
 * Home greeting block.
 *
 * Used ONLY on:
 *  - Business Home
 *  - Supplier Home
 *
 * This is plain scrolling content, NOT a header/nav bar -- BrandTopBar
 * owns all persistent chrome (including notifications) now. Previously
 * this component was styled like a floating card with its own bell,
 * which visually duplicated BrandTopBar. Simplified to a flat inline
 * row: greeting + name + avatar, no border/shadow/card, no bell.
 */
export function HomeHeader({ greeting, name, avatarLabel, onProfilePress }: HomeHeaderProps) {
  const theme = useTheme();

  return (
    <View style={styles.container}>
      <View style={styles.left}>
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
          {greeting}
        </Text>
        <Text variant="headlineSmall" style={styles.name}>
          {name}
        </Text>
      </View>

      <Pressable onPress={onProfilePress} hitSlop={6}>
        <Avatar.Text size={40} label={avatarLabel} />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: spacing.md,
    marginBottom: spacing.md,
  },
  left: {
    flex: 1,
  },
  name: {
    fontWeight: "700",
  },
});