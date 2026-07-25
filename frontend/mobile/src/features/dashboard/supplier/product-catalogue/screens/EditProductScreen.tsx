import React, { useState } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Snackbar } from 'react-native-paper';
import { ProductForm } from '../components/ProductForm';
import { useProduct } from '../hooks/useProducts';
import { useUpdateProduct } from '../hooks/useUpdateProduct';
import type { ProductCategory } from '../types';
import type { ProductFormValues } from '../services/productValidation';

// Placeholder categories until the Platform/Categories feature (GET
// /categories, Document 05 §5.7) is wired up.
const MOCK_CATEGORIES: ProductCategory[] = [
  { id: 'cat-beverages', name: 'Beverages', parentCategoryId: null },
  { id: 'cat-cleaning', name: 'Cleaning Supplies', parentCategoryId: null },
  { id: 'cat-packaging', name: 'Packaging', parentCategoryId: null },
];

export function EditProductScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { data: product, isLoading } = useProduct(id);
  const updateProduct = useUpdateProduct();
  const [errorVisible, setErrorVisible] = useState(false);

  if (isLoading || !product) {
    return <ActivityIndicator style={{ marginTop: 48 }} />;
  }

  // Capture id to ensure TypeScript narrows the type inside the closure
  const productId = product.id;

  function handleSubmit(values: ProductFormValues) {
    updateProduct.mutate(
      { id: productId, input: values },
      {
        onSuccess: () => router.back(),
        onError: () => setErrorVisible(true),
      },
    );
  }

  return (
    <View style={{ flex: 1 }}>
      <ProductForm
        categories={MOCK_CATEGORIES}
        initialValues={{
          categoryId: product.categoryId,
          name: product.name,
          description: product.description,
          price: product.price,
          unit: product.unit,
          minimumOrderQuantity: product.minimumOrderQuantity,
          stockStatus: product.stockStatus,
          isPublished: product.isPublished,
          bulkPricingRules: product.bulkPricingRules.map((tier) => ({
            minQuantity: tier.minQuantity,
            price: tier.price,
          })),
        }}
        onSubmit={handleSubmit}
        isSubmitting={updateProduct.isPending}
        submitLabel="Save Changes"
      />
      <Snackbar visible={errorVisible} onDismiss={() => setErrorVisible(false)}>
        Could not save changes. Please try again.
      </Snackbar>
    </View>
  );
}