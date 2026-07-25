import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Portal, Modal, Text, Button, SegmentedButtons } from 'react-native-paper';
import { ProductCategorySelector } from './ProductCategorySelector';
import { STOCK_STATUS_OPTIONS } from '../services/stockManager';
import type { ProductCategory, ProductFilters, StockStatus } from '../types';

interface Props {
  visible: boolean;
  onDismiss: () => void;
  categories: ProductCategory[];
  filters: ProductFilters;
  onChange: (filters: ProductFilters) => void;
  onApply: () => void;
  onClear: () => void;
}

/** Document 02 \u00a72.4 / \u00a75.11: modal-based filter sheet for list-based discovery screens. */
export function ProductFilterSheet({
  visible,
  onDismiss,
  categories,
  filters,
  onChange,
  onApply,
  onClear,
}: Props) {
  return (
    <Portal>
      <Modal visible={visible} onDismiss={onDismiss} contentContainerStyle={styles.container}>
        <Text variant="titleMedium" style={styles.title}>
          Filter Products
        </Text>

        <Text variant="labelLarge" style={styles.label}>
          Category
        </Text>
        <ProductCategorySelector
          categories={categories}
          selectedCategoryId={filters.categoryId ?? null}
          onSelect={(categoryId) => onChange({ ...filters, categoryId })}
        />

        <Text variant="labelLarge" style={styles.label}>
          Stock Status
        </Text>
        <SegmentedButtons
          value={filters.stockStatus ?? ''}
          onValueChange={(value) =>
            onChange({ ...filters, stockStatus: (value || undefined) as StockStatus | undefined })
          }
          buttons={[
            { value: '', label: 'Any' },
            ...STOCK_STATUS_OPTIONS.map((option) => ({ value: option.value, label: option.label })),
          ]}
        />

        <View style={styles.actions}>
          <Button onPress={onClear}>Clear</Button>
          <Button mode="contained" onPress={onApply}>
            Apply
          </Button>
        </View>
      </Modal>
    </Portal>
  );
}

const styles = StyleSheet.create({
  container: { backgroundColor: 'white', margin: 16, padding: 16, borderRadius: 12 },
  title: { marginBottom: 12 },
  label: { marginTop: 12, marginBottom: 6, opacity: 0.7 },
  actions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 8, marginTop: 20 },
});
