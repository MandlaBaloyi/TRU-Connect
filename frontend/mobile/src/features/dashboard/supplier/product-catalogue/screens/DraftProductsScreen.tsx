import React from 'react';
import { View, FlatList, StyleSheet } from 'react-native';
import { ActivityIndicator, Text } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { useProducts } from '../hooks/useProducts';
import { useUpdateProduct } from '../hooks/useUpdateProduct';
import { ProductCard } from '../components/ProductCard';
import type { Product } from '../types';

// See ProductCatalogueScreen.tsx for why this is '/product-catalogue'.
const ROUTE_BASE = '/product-catalogue';

/** Document 06 \u00a74: products saved as drafts (is_published = false). */
export function DraftProductsScreen() {
  const router = useRouter();
  const { data, isLoading } = useProducts({ publishedOnly: false });
  const updateProduct = useUpdateProduct();
  const drafts = (data?.products ?? []).filter((product) => !product.isPublished);

  function handleToggleAvailability(product: Product) {
    const next = product.stockStatus === 'in_stock' ? 'out_of_stock' : 'in_stock';
    updateProduct.mutate({ id: product.id, input: { stockStatus: next } });
  }

  if (isLoading) return <ActivityIndicator style={styles.loader} />;

  return (
    <View style={styles.container}>
      {drafts.length === 0 && <Text style={styles.empty}>No draft products.</Text>}
      <FlatList
        data={drafts}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <ProductCard
            product={item}
            onPress={(product) => router.push(`${ROUTE_BASE}/${product.id}`)}
            onEdit={(product) => router.push(`${ROUTE_BASE}/${product.id}/edit`)}
            onToggleAvailability={handleToggleAvailability}
          />
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  loader: { marginTop: 48 },
  empty: { textAlign: 'center', marginTop: 32, opacity: 0.7 },
});