import React from "react";
import { View, StyleSheet, Pressable, Platform } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { X } from "lucide-react-native";
import { spacing, radius } from "@/theme/spacing";

interface SectionHeaderProps {
  title: string;
  /** Omit to render a plain title with no close action. */
  onClosePress?: () => void;
}

// Must stay identical to HomeHeader's values so every dashboard screen
// shares the same nav-bar height, border, and corner treatment.
const HEADER_HEIGHT = 88;
const HEADER_BORDER_WIDTH = 1.5;
const HEADER_CORNER_RADIUS = radius.lg;

const CLOSE_TOUCH_TARGET = 44; // WCAG/HIG minimum touch target

/**
 * Title header for non-Home dashboard tabs
 * (Account, Community, Discovery, More).
 *
 * Home uses HomeHeader (greeting + avatar + bell). This mirrors its
 * height, background, border, and corner radius exactly so the nav bar
 * reads as one continuous system across every screen.
 *
 * Title is centered via absolute positioning (not flex order) so the
 * close button on the right never visually pushes it off-center.
 */
export function SectionHeader({ title, onClosePress }: SectionHeaderProps) {
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
      <Text
        variant="headlineSmall"
        style={styles.title}
        numberOfLines={1}
      >
        {title}
      </Text>

      {onClosePress && (
        <Pressable
          onPress={onClosePress}
          hitSlop={12}
          style={styles.closeButton}
          accessibilityRole="button"
          accessibilityLabel="Close"
        >
          <X size={30} color={theme.colors.onSurface} />
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    height: HEADER_HEIGHT,
    justifyContent: "center",

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
  title: {
    width: "100%",
    textAlign: "center",
    fontWeight: "700",
  },
  closeButton: {
    position: "absolute",
    right: spacing.sm,
    top: (HEADER_HEIGHT - CLOSE_TOUCH_TARGET) / 2,
    width: CLOSE_TOUCH_TARGET,
    height: CLOSE_TOUCH_TARGET,
    alignItems: "center",
    justifyContent: "center",
  },
});