import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Searchbar, IconButton } from 'react-native-paper';

interface Props {
  value: string;
  onChangeText: (text: string) => void;
  onFilterPress?: () => void;
  placeholder?: string;
}

/** Document 02 \u00a76: persistent search entry point for discovery-style screens. */
export function ProductSearchBar({
  value,
  onChangeText,
  onFilterPress,
  placeholder = 'Search your products',
}: Props) {
  return (
    <View style={styles.row}>
      <Searchbar
        placeholder={placeholder}
        value={value}
        onChangeText={onChangeText}
        style={styles.searchbar}
      />
      {onFilterPress && (
        <IconButton icon="filter-variant" onPress={onFilterPress} accessibilityLabel="Filter products" />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  searchbar: { flex: 1 },
});
