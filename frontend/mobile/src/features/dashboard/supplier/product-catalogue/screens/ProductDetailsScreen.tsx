import React, { useState } from 'react';
import { View, ScrollView, StyleSheet, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Button, Dialog, Portal, Text } from 'react-native-paper';
import { useProduct } from '../hooks/useProducts';
import { useDeleteProduct } from '../hooks/useDeleteProduct';
import { ProductStatusBadge } from '../components/ProductStatusBadge';
import { ProductPriceCard } from '../components/ProductPriceCard';

/** Supplier's own read view of a product (distinct from the business-facing Product Detail screen). */
export function ProductDetailsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { data: product, isLoading } = useProduct(id);
  const deleteProduct = useDeleteProduct();
  const [confirmVisible, setConfirmVisible] = useState(false);

  if (isLoading || !product) {
    return <ActivityIndicator style={{ marginTop: 48 }} />;
  }

  // capture product.id so TypeScript can narrow it inside handleDelete
  const productId = product.id;

  function handleDelete() {
    deleteProduct.mutate(productId, { onSuccess: () => router.back() });
    setConfirmVisible(false);
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text variant="headlineSmall">{product.name}</Text>
      <ProductStatusBadge product={product} />
      <Text variant="bodyMedium" style={styles.description}>
        {product.description}
      </Text>
      <ProductPriceCard product={product} />
      <Text variant="bodySmall" style={styles.meta}>
        Minimum order quantity: {product.minimumOrderQuantity} {product.unit}
      </Text>

      <View style={styles.actions}>
        <Button mode="outlined" onPress={() => router.push(`/product-catalogue/${productId}/edit`)}>
          Edit
        </Button>
        <Button mode="outlined" onPress={() => router.push(`/product-catalogue/${productId}/images`)}>
          Manage Images
        </Button>
        <Button mode="text" textColor="red" onPress={() => setConfirmVisible(true)}>
          Delete
        </Button>
      </View>

      <Portal>
        <Dialog visible={confirmVisible} onDismiss={() => setConfirmVisible(false)}>
          <Dialog.Title>Delete this product?</Dialog.Title>
          <Dialog.Content>
            <Text>
              This unpublishes the product and preserves any historical orders, per platform policy
              (Document 06 §4).
            </Text>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setConfirmVisible(false)}>Cancel</Button>
            <Button onPress={handleDelete}>Delete</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, gap: 12 },
  description: { marginTop: 4 },
  meta: { opacity: 0.7 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 16 },
});