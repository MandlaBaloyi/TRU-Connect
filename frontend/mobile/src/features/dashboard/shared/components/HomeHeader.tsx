import React from "react";
import { View, StyleSheet, Pressable, Platform } from "react-native";
import { Text, Avatar, Badge, useTheme } from "react-native-paper";
import { Bell } from "lucide-react-native";

import { spacing, radius } from "@/theme/spacing";

interface HomeHeaderProps {
  greeting: string;
  name: string;
  avatarLabel: string;

  unreadNotificationCount?: number;

  onNotificationsPress?: () => void;
  onProfilePress?: () => void;
}

// Shared with SectionHeader -- keep these values identical so every
// dashboard screen has the exact same nav-bar height, border, and
// corner treatment (see UI Refinement Prompt: "Visual Consistency").
const HEADER_HEIGHT = 88;
const HEADER_BORDER_WIDTH = 1.5;
const HEADER_CORNER_RADIUS = radius.lg;

/**
 * Home Dashboard Header
 *
 * Used ONLY on:
 *  - Business Home
 *  - Supplier Home
 *
 * Displays:
 *  - Greeting
 *  - Business/Supplier name
 *  - Notification Bell
 *  - Avatar
 */
export function HomeHeader({
  greeting,
  name,
  avatarLabel,
  unreadNotificationCount = 0,
  onNotificationsPress,
  onProfilePress,
}: HomeHeaderProps) {
  const theme = useTheme();

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: theme.colors.surface,
          borderBottomColor: theme.colors.outlineVariant,
        },
      ]}
    >
      <View style={styles.left}>
        <Text
          variant="bodyMedium"
          style={{ color: theme.colors.onSurfaceVariant }}
        >
          {greeting}
        </Text>

        <Text variant="headlineSmall" style={styles.name}>
          {name}
        </Text>
      </View>

      <View style={styles.right}>
        <Pressable
          onPress={onNotificationsPress}
          hitSlop={10}
          style={styles.notificationButton}
        >
          <Bell
            size={22}
            color={theme.colors.onSurface}
          />

          {unreadNotificationCount > 0 && (
            <Badge
              size={16}
              style={styles.badge}
            >
              {unreadNotificationCount}
            </Badge>
          )}
        </Pressable>

        <Pressable
          onPress={onProfilePress}
          hitSlop={6}
        >
          <Avatar.Text
            size={40}
            label={avatarLabel}
          />
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    height: HEADER_HEIGHT,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",

    paddingHorizontal: spacing.md,

    borderWidth: HEADER_BORDER_WIDTH,
    borderRadius: HEADER_CORNER_RADIUS,

    marginBottom: spacing.md,

    ...Platform.select({
      ios: {
        shadowColor: "#000",
        shadowOpacity: 0.05,
        shadowOffset: { width: 0, height: 2 },
        shadowRadius: 6,
      },
      android: {
        elevation: 3,
      },
    }),
  },

  left: {
    flex: 1,
  },

  name: {
    fontWeight: "700",
  },

  right: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
  },

  notificationButton: {
    padding: spacing.xs,
  },

  badge: {
    position: "absolute",
    top: 0,
    right: 0,
  },
});