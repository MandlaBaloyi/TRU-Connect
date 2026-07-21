import React, { useEffect, useRef } from "react";
import { View, Pressable, StyleSheet, Animated, Dimensions, Platform } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { Ionicons } from "@expo/vector-icons";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import type { BottomTabBarProps } from "@react-navigation/bottom-tabs";
import { spacing, radius } from "@/theme/spacing";

const { width: SCREEN_WIDTH } = Dimensions.get("window");
const IS_SMALL_DEVICE = SCREEN_WIDTH < 360;

// Overall bar height, ~12% taller than the previous 64px baseline.
const BAR_HEIGHT = 72;

const ICONS: Record <
  string,
  { active: keyof typeof Ionicons.glyphMap; inactive: keyof typeof Ionicons.glyphMap }
> = {
  home: { active: "home", inactive: "home-outline" },
  account: { active: "person", inactive: "person-outline" },
  community: { active: "people", inactive: "people-outline" },
  discovery: { active: "compass", inactive: "compass-outline" },
  more: { active: "ellipsis-horizontal", inactive: "ellipsis-horizontal-outline" },
};

interface TabItemProps {
  routeName: string;
  isFocused: boolean;
  label: string;
  onPress: () => void;
  onLongPress: () => void;
}

function TabItem({ routeName, isFocused, label, onPress, onLongPress }: TabItemProps) {
  const theme = useTheme();
  const anim = useRef(new Animated.Value(isFocused ? 1 : 0)).current;

  useEffect(() => {
    Animated.spring(anim, {
      toValue: isFocused ? 1 : 0,
      useNativeDriver: false,
      speed: 18,
      bounciness: 6,
    }).start();
  }, [isFocused, anim]);

  const icons = ICONS[routeName] ?? ICONS.home;
  const iconSize = IS_SMALL_DEVICE ? 22 : 24;

  const pillBackground = anim.interpolate({
    inputRange: [0, 1],
    outputRange: ["transparent", theme.colors.primaryContainer],
  });

  const iconScale = anim.interpolate({
    inputRange: [0, 1],
    outputRange: [1, 1.06],
  });

  return (
    <Pressable
      onPress={onPress}
      onLongPress={onLongPress}
      android_ripple={{ color: theme.colors.primaryContainer, borderless: true, radius: 28 }}
      hitSlop={8}
      style={styles.item}
      accessibilityRole="tab"
      accessibilityState={{ selected: isFocused }}
      accessibilityLabel={label}
    >
      <Animated.View
        style={[
          styles.pill,
          { backgroundColor: pillBackground, transform: [{ scale: iconScale }] },
        ]}
      >
        <Ionicons
          name={isFocused ? icons.active : icons.inactive}
          size={iconSize}
          color={isFocused ? theme.colors.primary : theme.colors.onSurfaceVariant}
        />
      </Animated.View>

      <Text
        numberOfLines={1}
        style={[
          styles.label,
          {
            color: isFocused ? theme.colors.primary : theme.colors.onSurfaceVariant,
            fontWeight: isFocused ? "700" : "500",
          },
        ]}
      >
        {label}
      </Text>
    </Pressable>
  );
}

/**
 * Custom bottom tab bar shared by Business & Supplier dashboards.
 *
 * Design goals (matching modern flagship-app patterns):
 *  - Animated pill highlight behind the active icon instead of a flat
 *    colour swap -- reads as intentional, not default RN styling
 *  - Safe-area aware bottom padding so it never collides with the
 *    home indicator on notched/gesture-nav devices
 *  - Responsive icon/label sizing on small-width phones
 *  - Subtle elevation instead of a harsh drop shadow
 *
 * Icon source of truth lives here (ICONS map above) rather than being
 * repeated as tabBarIcon per <Tabs.Screen>, so Business and Supplier
 * layouts stay tiny and in sync.
 */
export function DashboardTabBar({ state, descriptors, navigation }: BottomTabBarProps) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: theme.colors.surface,
          borderTopColor: theme.colors.outlineVariant,
          paddingBottom: Math.max(insets.bottom, spacing.sm + 2),
        },
      ]}
    >
      {state.routes.map((route, index) => {
        const { options } = descriptors[route.key];
        const label = typeof options.title === "string" ? options.title : route.name;
        const isFocused = state.index === index;

        const onPress = () => {
          const event = navigation.emit({
            type: "tabPress",
            target: route.key,
            canPreventDefault: true,
          });
          if (!isFocused && !event.defaultPrevented) {
            navigation.navigate(route.name);
          }
        };

        const onLongPress = () => {
          navigation.emit({ type: "tabLongPress", target: route.key });
        };

        return (
          <TabItem
            key={route.key}
            routeName={route.name}
            isFocused={isFocused}
            label={label}
            onPress={onPress}
            onLongPress={onLongPress}
          />
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    minHeight: BAR_HEIGHT,
    flexDirection: "row",
    borderTopWidth: 1,
    paddingTop: spacing.sm + 2,
    paddingHorizontal: spacing.xs,

    ...Platform.select({
      ios: {
        shadowColor: "#000",
        shadowOpacity: 0.04,
        shadowOffset: { width: 0, height: -2 },
        shadowRadius: 8,
      },
      android: {
        elevation: 8,
      },
    }),
  },
  item: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 2,
  },
  pill: {
    width: 48,
    height: 34,
    borderRadius: radius.pill,
    alignItems: "center",
    justifyContent: "center",
  },
  label: {
    fontSize: IS_SMALL_DEVICE ? 10 : 11,
  },
});