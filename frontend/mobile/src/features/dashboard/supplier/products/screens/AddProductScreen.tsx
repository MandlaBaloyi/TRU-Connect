/**
 * AddProductScreen — thin wrapper around ProductForm. This screen only
 * owns the CREATE action; the field set itself lives in ProductForm
 * since EditProductScreen needs the identical fields.
 *
 * TWO CALLS ON SUBMIT, NOT ONE -- create the Product (products/api),
 * then (only if a starting quantity was given) seed its Inventory
 * record via inventory/api directly. Products and Inventory stay two
 * separate resources with two separate APIs (see inventory/types.ts's
 * own "never duplicates product data" docstring) -- this screen is
 * where the two get orchestrated together, not either API reaching
 * into the other. A zero starting quantity skips the second call
 * entirely: Inventory's own getOrCreateInventoryItem already lazily
 * creates a 0-quantity record the first time anything looks this
 * product up, so there's nothing to seed.
 */

import React, { useState } from "react";
import { useRouter } from "expo-router";

import { useCreateProduct } from "../hooks";
import { ProductsError } from "../types";
import { ProductForm, type ProductFormValues } from "../components/ProductForm";
import { adjustStock } from "../../inventory/api/inventoryApi";
import { ScreenContainer } from "@/components/ui/ScreenContainer";

export default function AddProductScreen() {
  const router = useRouter();
  const { createProduct, isCreating } = useCreateProduct();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleSubmit = async (values: ProductFormValues) => {
    setSubmitError(null);
    setFieldErrors({});
    try {
      const product = await createProduct({
        name: values.name,
        category: values.category,
        priceCents: values.priceCents,
        compareAtPriceCents: values.compareAtPriceCents,
        sellingUnit: values.sellingUnit,
        description: values.description,
        sku: values.sku,
        localImageUris: values.images,
      });

      if (values.startingQuantity && values.startingQuantity > 0) {
        await adjustStock({
          productId: product.id,
          quantityDelta: values.startingQuantity,
          reason: "STOCK_RECEIVED",
        });
      }

      router.back();
    } catch (error) {
      if (error instanceof ProductsError) {
        setFieldErrors(error.fieldErrors);
        setSubmitError(error.message);
      } else {
        setSubmitError("Couldn't add this product. Check your connection and try again.");
      }
    }
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ProductForm
        isCreating
        onSubmit={handleSubmit}
        submitLabel="Add Product"
        isSubmitting={isCreating}
        fieldErrors={fieldErrors}
        submitError={submitError}
      />
    </ScreenContainer>
  );
}
