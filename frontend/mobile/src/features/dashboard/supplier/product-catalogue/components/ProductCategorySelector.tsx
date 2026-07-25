import React from 'react';
import { ScrollView, StyleSheet } from 'react-native';
import { Chip } from 'react-native-paper';
import type { ProductCategory } from '../types';

interface Props {
  categories: ProductCategory[];
  selectedCategoryId: string | null;
  onSelect: (categoryId: string) => void;
}

/**
 * Presentational only. Category data itself belongs to the Platform Domain
 * (GET /categories, Document 05 \u00a75.7) and is intentionally not fetched
 * here, to avoid mixing an unrelated feature's data-fetching into the
 * Product Catalogue feature (project instruction: build one feature at a
 * time). Screens currently pass in a local mock category list -- swap for
 * a shared useCategories() hook once the Platform/Categories feature
 * exists.
 */
export function ProductCategorySelector({ categories, selectedCategoryId, onSelect }: Props) {
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
      {categories.map((category) => (
        <Chip
          key={category.id}
          selected={category.id === selectedCategoryId}
          onPress={() => onSelect(category.id)}
          style={styles.chip}
        >
          {category.name}
        </Chip>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: { gap: 8, paddingVertical: 4 },
  chip: { marginRight: 4 },
});
