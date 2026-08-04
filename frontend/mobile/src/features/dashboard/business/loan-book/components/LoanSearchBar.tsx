/**
 * LoanSearchBar — customer search. Theme-aware.
 */

import React from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useTheme } from "react-native-paper";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  value: string;
  onChangeText: (text: string) => void;
  onClear?: () => void;
  placeholder?: string;
  label?: string;
}

export function LoanSearchBar({
  value,
  onChangeText,
  onClear,
  placeholder = "Name or phone number",
  label = "Find a customer",
}: Props) {
  const theme = useTheme();
  return (
    <View style={styles.wrapper}>
      <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>{label}</Text>
      <View style={[styles.field, { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface }]}>
        <TextInput
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={theme.colors.onSurfaceVariant}
          style={[styles.input, { color: theme.colors.onSurface }]}
          autoCorrect={false}
          autoCapitalize="words"
          returnKeyType="search"
          accessibilityLabel={label}
        />
        {value.length > 0 && onClear && (
          <Pressable onPress={onClear} hitSlop={12} accessibilityRole="button" accessibilityLabel="Clear search">
            <Text style={{ color: theme.colors.onSurfaceVariant, fontSize: 15 }}>✕</Text>
          </Pressable>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: spacing.xs },
  label: { ...typography.bodySmall },
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
