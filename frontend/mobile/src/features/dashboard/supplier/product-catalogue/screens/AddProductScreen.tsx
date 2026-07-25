import React, { useState } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { Snackbar } from 'react-native-paper';
import { ProductForm } from '../components/ProductForm';
import { useCreateProduct } from '../hooks/useCreateProduct';
import type { ProductCategory } from '../types';
import type { ProductFormValues } from '../services/productValidation';

// Placeholder categories until the Platform/Categories feature (GET
// /categories, Document 05 \u00a75.7) is wired up.
const MOCK_CATEGORIES: ProductCategory[] = [
  { id: 'cat-beverages', name: 'Beverages', parentCategoryId: null },
  { id: 'cat-cleaning', name: 'Cleaning Supplies', parentCategoryId: null },
  { id: 'cat-packaging', name: 'Packaging', parentCategoryId: null },
];

export function AddProductScreen() {
  const router = useRouter();
  const createProduct = useCreateProduct();
  const [errorVisible, setErrorVisible] = useState(false);

  function handleSubmit(values: ProductFormValues) {
    createProduct.mutate(
      { ...values, bulkPricingRules: values.bulkPricingRules ?? [] },
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
        onSubmit={handleSubmit}
        isSubmitting={createProduct.isPending}
        submitLabel="Create Product"
      />
      <Snackbar visible={errorVisible} onDismiss={() => setErrorVisible(false)}>
        Could not create the product. Please try again.
      </Snackbar>
    </View>
  );
}
