import React, { useMemo } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button, HelperText, SegmentedButtons, Switch, Text, TextInput } from 'react-native-paper';
import { productSchema, ProductFormValues, validateBulkPricingTiers } from '../services/productValidation';
import { ProductCategorySelector } from './ProductCategorySelector';
import type { ProductCategory } from '../types';
import { STOCK_STATUS_OPTIONS } from '../services/stockManager';

interface Props {
  categories: ProductCategory[];
  initialValues?: Partial<ProductFormValues>;
  onSubmit: (values: ProductFormValues) => void;
  isSubmitting?: boolean;
  submitLabel?: string;
}

const DEFAULT_VALUES: ProductFormValues = {
  categoryId: '',
  name: '',
  description: '',
  price: 0,
  unit: 'each',
  minimumOrderQuantity: 1,
  stockStatus: 'in_stock',
  isPublished: false,
  bulkPricingRules: [],
};

/**
 * Single-page product create/edit form. Document 02 \u00a79 recommends a step
 * indicator for multi-step forms -- Add/Edit Product is intentionally kept
 * single-page for Phase 1 given its relatively small field count; revisit
 * as a stepper if the form grows.
 */
export function ProductForm({
  categories,
  initialValues,
  onSubmit,
  isSubmitting,
  submitLabel = 'Save Product',
}: Props) {
  const {
    control,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ProductFormValues>({
    resolver: zodResolver(productSchema),
    defaultValues: { ...DEFAULT_VALUES, ...initialValues },
  });

  const bulkPricingRules = watch('bulkPricingRules') ?? [];
  const bulkPricingError = useMemo(
    () => validateBulkPricingTiers(bulkPricingRules),
    [bulkPricingRules],
  );

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text variant="labelLarge">Product Name</Text>
      <Controller
        control={control}
        name="name"
        render={({ field }) => (
          <TextInput mode="outlined" value={field.value} onChangeText={field.onChange} />
        )}
      />
      <HelperText type="error" visible={!!errors.name}>
        {errors.name?.message}
      </HelperText>

      <Text variant="labelLarge">Description</Text>
      <Controller
        control={control}
        name="description"
        render={({ field }) => (
          <TextInput
            mode="outlined"
            multiline
            numberOfLines={4}
            value={field.value}
            onChangeText={field.onChange}
          />
        )}
      />
      <HelperText type="error" visible={!!errors.description}>
        {errors.description?.message}
      </HelperText>

      <Text variant="labelLarge">Category</Text>
      <Controller
        control={control}
        name="categoryId"
        render={({ field }) => (
          <ProductCategorySelector
            categories={categories}
            selectedCategoryId={field.value}
            onSelect={field.onChange}
          />
        )}
      />
      <HelperText type="error" visible={!!errors.categoryId}>
        {errors.categoryId?.message}
      </HelperText>

      <View style={styles.rowFields}>
        <View style={styles.flexField}>
          <Text variant="labelLarge">Price (ZAR)</Text>
          <Controller
            control={control}
            name="price"
            render={({ field }) => (
              <TextInput
                mode="outlined"
                keyboardType="decimal-pad"
                value={String(field.value)}
                onChangeText={(text) => field.onChange(Number(text) || 0)}
              />
            )}
          />
          <HelperText type="error" visible={!!errors.price}>
            {errors.price?.message}
          </HelperText>
        </View>
        <View style={styles.flexField}>
          <Text variant="labelLarge">Unit</Text>
          <Controller
            control={control}
            name="unit"
            render={({ field }) => (
              <TextInput mode="outlined" value={field.value} onChangeText={field.onChange} />
            )}
          />
          <HelperText type="error" visible={!!errors.unit}>
            {errors.unit?.message}
          </HelperText>
        </View>
      </View>

      <Text variant="labelLarge">Minimum Order Quantity</Text>
      <Controller
        control={control}
        name="minimumOrderQuantity"
        render={({ field }) => (
          <TextInput
            mode="outlined"
            keyboardType="number-pad"
            value={String(field.value)}
            onChangeText={(text) => field.onChange(Number(text) || 0)}
          />
        )}
      />
      <HelperText type="error" visible={!!errors.minimumOrderQuantity}>
        {errors.minimumOrderQuantity?.message}
      </HelperText>

      <Text variant="labelLarge">Stock Status</Text>
      <Controller
        control={control}
        name="stockStatus"
        render={({ field }) => (
          <SegmentedButtons
            value={field.value}
            onValueChange={field.onChange}
            buttons={STOCK_STATUS_OPTIONS.map((option) => ({ value: option.value, label: option.label }))}
          />
        )}
      />

      {bulkPricingError && (
        <HelperText type="error" visible>
          {bulkPricingError}
        </HelperText>
      )}

      <View style={styles.publishRow}>
        <Text variant="labelLarge">Publish this product</Text>
        <Controller
          control={control}
          name="isPublished"
          render={({ field }) => <Switch value={field.value} onValueChange={field.onChange} />}
        />
      </View>

      <Button
        mode="contained"
        onPress={handleSubmit(onSubmit)}
        loading={isSubmitting}
        disabled={isSubmitting || !!bulkPricingError}
        style={styles.submitButton}
      >
        {submitLabel}
      </Button>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, gap: 4 },
  rowFields: { flexDirection: 'row', gap: 12 },
  flexField: { flex: 1 },
  publishRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginVertical: 16,
  },
  submitButton: { marginTop: 8, marginBottom: 32 },
});
