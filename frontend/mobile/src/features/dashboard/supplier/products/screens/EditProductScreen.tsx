/**
 * EditProductScreen — thin wrapper around ProductForm, same pattern as
 * AddProductScreen. Only owns the UPDATE action and seeding the form
 * from the existing product; the field set itself is ProductForm's.
 *
 * No quantity field here at all -- per ProductForm's own docstring,
 * once a product has a real Inventory record, quantity has exactly
 * one place it changes: Inventory's own Adjust Stock screen.
 */

import React, { useState } from "react";
import { ActivityIndicator, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { useProduct, useUpdateProduct } from "../hooks";
import { ProductsError } from "../types";
import { ProductForm, type ProductFormValues } from "../components/ProductForm";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";

export default function EditProductScreen() {
  const { productId } = useLocalSearchParams<{ productId: string }>();
  const router = useRouter();
  const theme = useTheme();

  const { product, isLoading, isError, refetch } = useProduct(productId ?? "");
  const { updateProduct, isUpdating } = useUpdateProduct();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleSubmit = async (values: ProductFormValues) => {
    if (!product) return;
    setSubmitError(null);
    setFieldErrors({});
    try {
      await updateProduct({
        id: product.id,
        name: values.name,
        category: values.category,
        priceCents: values.priceCents,
        compareAtPriceCents: values.compareAtPriceCents,
        sellingUnit: values.sellingUnit,
        unitQuantity: values.unitQuantity,
        unitMeasure: values.unitMeasure,
        description: values.description,
        sku: values.sku,
        images: values.images,
      });
      router.back();
    } catch (error) {
      if (error instanceof ProductsError) {
        setFieldErrors(error.fieldErrors);
        setSubmitError(error.message);
      } else {
        setSubmitError("Couldn't save changes. Check your connection and try again.");
      }
    }
  };

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !product) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load this product. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader>
      <ProductForm
        isCreating={false}
        initialValues={{
          name: product.name,
          category: product.category,
          priceCents: product.priceCents,
          compareAtPriceCents: product.compareAtPriceCents ?? undefined,
          sellingUnit: product.sellingUnit,
          description: product.description ?? undefined,
          sku: product.sku,
          images: product.images,
        }}
        onSubmit={handleSubmit}
        submitLabel="Save Changes"
        isSubmitting={isUpdating}
        fieldErrors={fieldErrors}
        submitError={submitError}
      />
    </ScreenContainer>
  );
}
