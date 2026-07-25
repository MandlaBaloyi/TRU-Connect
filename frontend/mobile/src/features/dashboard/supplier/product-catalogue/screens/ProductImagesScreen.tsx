import React from 'react';
import { View, StyleSheet, ActivityIndicator } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { Text } from 'react-native-paper';
import { useQueryClient } from '@tanstack/react-query';
import { useProduct, productCatalogueQueryKeys } from '../hooks/useProducts';
import { productCatalogueApi } from '../api/productCatalogueApi';
import { ProductImageUploader } from '../components/ProductImageUploader';

export function ProductImagesScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data: product, isLoading } = useProduct(id);
  const queryClient = useQueryClient();

  if (isLoading || !product) {
    return <ActivityIndicator style={styles.loader} />;
  }

  async function handleAdd(localUri: string) {
    await productCatalogueApi.addImage(product!.id, localUri);
    queryClient.invalidateQueries({ queryKey: productCatalogueQueryKeys.detail(product!.id) });
  }

  async function handleRemove(imageId: string) {
    await productCatalogueApi.removeImage(product!.id, imageId);
    queryClient.invalidateQueries({ queryKey: productCatalogueQueryKeys.detail(product!.id) });
  }

  return (
    <View style={styles.container}>
      <Text variant="titleMedium" style={styles.title}>
        Product Images
      </Text>
      <ProductImageUploader images={product.images} onAdd={handleAdd} onRemove={handleRemove} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  loader: { marginTop: 48 },
  title: { marginBottom: 12 },
});
