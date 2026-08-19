import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  onAddProduct?: () => void;
  variant?: "FIRST_RUN" | "NO_RESULTS";
  onClearFilters?: () => void;
}

export function EmptyProducts({ onAddProduct, variant = "FIRST_RUN", onClearFilters }: Props) {
  const theme = useTheme();

  if (variant === "NO_RESULTS") {
    return (
      <View style={styles.wrapper}>
        <Text style={styles.icon}>🔍</Text>
        <Text style={[styles.title, { color: theme.colors.onBackground }]}>No products found</Text>
        <Text style={[styles.body, { color: theme.colors.onSurfaceVariant }]}>
          Try a different search, or clear the filters.
        </Text>
        {onClearFilters && (
          <Pressable
            onPress={onClearFilters}
            style={[styles.action, { backgroundColor: theme.colors.primary }]}
            accessibilityRole="button"
          >
            <Text style={[styles.actionText, { color: theme.colors.onPrimary }]}>Clear filters</Text>
          </Pressable>
        )}
      </View>
    );
  }

  return (
    <View style={styles.wrapper}>
      <Text style={styles.icon}>📦</Text>
      <Text style={[styles.title, { color: theme.colors.onBackground }]}>No products yet</Text>
      <Text style={[styles.body, { color: theme.colors.onSurfaceVariant }]}>
        Add what you sell so connected businesses can find it.
      </Text>
      {onAddProduct && (
        <Pressable
          onPress={onAddProduct}
          style={[styles.action, { backgroundColor: theme.colors.primary }]}
          accessibilityRole="button"
        >
          <Text style={[styles.actionText, { color: theme.colors.onPrimary }]}>Add your first product</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { alignItems: "center", paddingVertical: spacing.xxl, paddingHorizontal: spacing.lg, gap: spacing.sm },
  icon: { fontSize: 40 },
  title: { ...typography.h1, textAlign: "center" },
  body: { ...typography.body, textAlign: "center" },
  action: {
    marginTop: spacing.md,
    minHeight: 48,
    justifyContent: "center",
    paddingHorizontal: spacing.lg,
    borderRadius: radius.md,
  },
  actionText: { ...typography.body, fontWeight: "600" },
});
