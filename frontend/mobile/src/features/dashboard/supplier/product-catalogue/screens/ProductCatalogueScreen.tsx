import React, { useState } from 'react';
import { View, FlatList, StyleSheet } from 'react-native';
import { ActivityIndicator, FAB, Text } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { useProductSearch } from '../hooks/useProductSearch';
import { useUpdateProduct } from '../hooks/useUpdateProduct';
import { ProductSearchBar } from '../components/ProductSearchBar';
import { ProductFilterSheet } from '../components/ProductFilterSheet';
import { ProductCard } from '../components/ProductCard';
import type { Product, ProductCategory, ProductFilters } from '../types';

// Placeholder categories until the Platform/Categories feature (GET
// /categories, Document 05 \u00a75.7) is wired up.
const MOCK_CATEGORIES: ProductCategory[] = [
  { id: 'cat-beverages', name: 'Beverages', parentCategoryId: null },
  { id: 'cat-cleaning', name: 'Cleaning Supplies', parentCategoryId: null },
  { id: 'cat-packaging', name: 'Packaging', parentCategoryId: null },
];

// product-catalogue now lives at app/(dashboard)/supplier/product-catalogue/,
// outside the (tabs) group. Route groups in parentheses never appear in the
// actual URL, so the href is just '/product-catalogue'.
const ROUTE_BASE = '/product-catalogue';

export function ProductCatalogueScreen() {
  const router = useRouter();
  const [filters, setFilters] = useState<ProductFilters>({});
  const [filterVisible, setFilterVisible] = useState(false);
  const { inputValue, setInputValue, data, isLoading, isError } = useProductSearch(filters);
  const updateProduct = useUpdateProduct();

  function handleToggleAvailability(product: Product) {
    const next = product.stockStatus === 'in_stock' ? 'out_of_stock' : 'in_stock';
    updateProduct.mutate({ id: product.id, input: { stockStatus: next } });
  }

  return (
    <View style={styles.container}>
      <ProductSearchBar
        value={inputValue}
        onChangeText={setInputValue}
        onFilterPress={() => setFilterVisible(true)}
      />

      {isLoading && <ActivityIndicator style={styles.loader} />}
      {isError && <Text style={styles.error}>Something went wrong loading your products.</Text>}

      {!isLoading && data?.products.length === 0 && (
        <View style={styles.empty}>
          <Text variant="titleMedium">No products yet</Text>
          <Text variant="bodyMedium">Add your first product to start selling on TRU Connect.</Text>
        </View>
      )}

      <FlatList
        data={data?.products ?? []}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <ProductCard
            product={item}
            onPress={(product) => router.push(`${ROUTE_BASE}/${product.id}`)}
            onEdit={(product) => router.push(`${ROUTE_BASE}/${product.id}/edit`)}
            onToggleAvailability={handleToggleAvailability}
          />
        )}
        contentContainerStyle={styles.list}
      />

      <ProductFilterSheet
        visible={filterVisible}
        onDismiss={() => setFilterVisible(false)}
        categories={MOCK_CATEGORIES}
        filters={filters}
        onChange={setFilters}
        onApply={() => setFilterVisible(false)}
        onClear={() => {
          setFilters({});
          setFilterVisible(false);
        }}
      />

      <FAB icon="plus" style={styles.fab} onPress={() => router.push(`${ROUTE_BASE}/add`)} label="Add Product" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, gap: 12 },
  list: { paddingBottom: 96 },
  loader: { marginTop: 24 },
  error: { color: 'red', marginTop: 16 },
  empty: { alignItems: 'center', marginTop: 48, gap: 8 },
  fab: { position: 'absolute', right: 16, bottom: 16 },
});