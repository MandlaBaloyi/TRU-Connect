import React from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";
import { TextInput, useTheme } from "react-native-paper";
import { Search } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { AddressSuggestion } from "../types";

interface Props {
  query: string;
  onChangeQuery: (text: string) => void;
  suggestions: AddressSuggestion[];
  isLoading: boolean;
  onSelect: (suggestion: AddressSuggestion) => void;
}

/**
 * The second of the two ways to set a location, offered as its own
 * separate entry point (SearchAddressModal) alongside "Choose on
 * map" -- NOT stacked on top of the map itself. That combined layout
 * was tried first and live testing showed it looking broken (the
 * dropdown fighting the map for the same cramped space), so this bar
 * now lives on its own full screen with room to breathe. The dropdown
 * is a plain absolutely-positioned overlay under the field -- still
 * simple, since even on its own screen nothing else here competes
 * for the same space below the input.
 */
export function SearchAddressBar({ query, onChangeQuery, suggestions, isLoading, onSelect }: Props) {
  const theme = useTheme();
  const showDropdown = query.trim().length > 0 && (suggestions.length > 0 || isLoading);

  return (
    <View style={styles.container}>
      <TextInput
        mode="outlined"
        label="Search for your address"
        value={query}
        onChangeText={onChangeQuery}
        left={<TextInput.Icon icon={() => <Search size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />} />}
        right={isLoading ? <TextInput.Icon icon={() => <ActivityIndicator size="small" />} /> : undefined}
        contentStyle={styles.inputContent}
      />
      {showDropdown && (
        <View style={[styles.dropdown, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outline }]}>
          {suggestions.length === 0 && !isLoading && (
            <Text style={[styles.emptyText, { color: theme.colors.onSurfaceVariant }]}>No matches -- try the map instead</Text>
          )}
          {suggestions.map((suggestion) => (
            <Pressable
              key={suggestion.mapboxId}
              onPress={() => onSelect(suggestion)}
              style={({ pressed }) => [styles.row, pressed && { backgroundColor: theme.colors.surfaceVariant }]}
              accessibilityRole="button"
              accessibilityLabel={suggestion.name}
            >
              <Text style={[styles.rowTitle, { color: theme.colors.onSurface }]} numberOfLines={1}>
                {suggestion.name}
              </Text>
              {suggestion.fullAddress && (
                <Text style={[styles.rowSubtitle, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
                  {suggestion.fullAddress}
                </Text>
              )}
            </Pressable>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { position: "relative", zIndex: 20 },
  inputContent: { paddingVertical: 2 },
  dropdown: {
    position: "absolute",
    top: "100%",
    left: 0,
    right: 0,
    marginTop: spacing.xs,
    borderWidth: 1,
    borderRadius: radius.md,
    overflow: "hidden",
    elevation: 4,
    shadowColor: "#000",
    shadowOpacity: 0.15,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
  },
  row: { paddingVertical: spacing.sm, paddingHorizontal: spacing.sm },
  rowTitle: { ...typography.body, fontWeight: "600" },
  rowSubtitle: { ...typography.caption, marginTop: 2 },
  emptyText: { ...typography.bodySmall, padding: spacing.sm },
});
