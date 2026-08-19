import React from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useTheme } from "react-native-paper";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  value: string;
  onChangeText: (text: string) => void;
  onClear?: () => void;
}

/**
 * Local/instant filtering only -- the list is already loaded, so
 * typing "coca" must never trigger a network request per keystroke.
 * Same input shape as Order Book's OrderSearchBar, this feature's own
 * copy per this codebase's established per-feature-component
 * convention.
 */
export function ProductSearchBar({ value, onChangeText, onClear }: Props) {
  const theme = useTheme();
  return (
    <View style={[styles.field, { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface }]}>
      <TextInput
        value={value}
        onChangeText={onChangeText}
        placeholder="Search products..."
        placeholderTextColor={theme.colors.onSurfaceVariant}
        style={[styles.input, { color: theme.colors.onSurface }]}
        autoCorrect={false}
        autoCapitalize="none"
        returnKeyType="search"
        accessibilityLabel="Search products"
      />
      {value.length > 0 && onClear && (
        <Pressable onPress={onClear} hitSlop={12} accessibilityRole="button" accessibilityLabel="Clear search">
          <Text style={{ color: theme.colors.onSurfaceVariant, fontSize: 15 }}>✕</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  field: {
    flexDirection: "row",
    alignItems: "center",
    minHeight: 48,
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    gap: spacing.sm,
  },
  input: { flex: 1, ...typography.body, paddingVertical: spacing.sm },
});
