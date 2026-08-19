/**
 * ProductForm — the shared field set behind Add Product AND Edit
 * Product. Owns its own field state, seeded from `initialValues` when
 * editing; the calling screen only owns the SUBMIT action (create vs.
 * update) and whatever loading/error state that specific mutation
 * needs.
 *
 * v2, POST-INVENTORY-MIGRATION: the old "Stock: In stock / Out of
 * stock" radio is GONE -- stock status is now computed by Inventory
 * from real quantity, not manually toggled here (see inventory/
 * types.ts's own docstring for the full reasoning). In its place:
 *
 * - CREATE (no initialValues): a "Starting quantity" number field.
 *   A brand-new product has no Inventory record yet, so something has
 *   to seed one -- this is that something. Optional, defaults to 0
 *   (an honest "nothing received yet" state, not a guess).
 * - EDIT (initialValues present): NO quantity field at all. Once a
 *   product has a real Inventory record, quantity has exactly one
 *   place it's changed -- Inventory's own Adjust Stock screen -- so
 *   Edit Product doesn't grow a second, competing way to change the
 *   same number.
 */

import React, { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { Cents, ProductCategory, ProductUnit } from "../types";
import { CATEGORY_OPTIONS, UNIT_OPTIONS } from "../types";
import { formatCents, parseCentsInput } from "../services/productMapper";
import { ProductPhotosField } from "./ProductPhotosField";
import { SelectFieldModal } from "./SelectFieldModal";
import { SelectFieldRow } from "./SelectFieldRow";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

export interface ProductFormValues {
  name: string;
  category: ProductCategory;
  priceCents: Cents;
  sellingUnit: ProductUnit;
  images: string[];
  /** Only meaningful on CREATE -- see this file's own header docstring.
   *  Undefined when editing (the field isn't rendered at all then). */
  startingQuantity?: number;
}

interface Props {
  initialValues?: Partial<ProductFormValues>;
  /** True for Add Product, false for Edit Product -- the one thing
   *  that decides whether the Starting quantity field renders. */
  isCreating: boolean;
  onSubmit: (values: ProductFormValues) => void | Promise<void>;
  submitLabel: string;
  isSubmitting: boolean;
  fieldErrors: Record<string, string>;
  submitError: string | null;
}

function labelFor<T extends string>(options: { value: T; label: string }[], value: T): string {
  return options.find((o) => o.value === value)?.label ?? value;
}

export function ProductForm({
  initialValues,
  isCreating,
  onSubmit,
  submitLabel,
  isSubmitting,
  fieldErrors,
  submitError,
}: Props) {
  const theme = useTheme();

  const [images, setImages] = useState<string[]>(initialValues?.images ?? []);
  const [name, setName] = useState(initialValues?.name ?? "");
  const [category, setCategory] = useState<ProductCategory>(initialValues?.category ?? "OTHER");
  const [categoryPickerOpen, setCategoryPickerOpen] = useState(false);
  const [priceText, setPriceText] = useState(
    initialValues?.priceCents !== undefined ? String(initialValues.priceCents / 100) : ""
  );
  const [sellingUnit, setSellingUnit] = useState<ProductUnit>(initialValues?.sellingUnit ?? "EACH");
  const [unitPickerOpen, setUnitPickerOpen] = useState(false);
  const [quantityText, setQuantityText] = useState("");

  const priceCents = parseCentsInput(priceText);
  const quantity = quantityText.trim() === "" ? 0 : Number.parseInt(quantityText, 10);
  const isValidQuantity = Number.isFinite(quantity) && quantity >= 0;
  const canSubmit = name.trim().length > 0 && priceCents !== null && (!isCreating || isValidQuantity) && !isSubmitting;

  const handleSubmit = () => {
    if (priceCents === null || (isCreating && !isValidQuantity)) return;
    onSubmit({
      name: name.trim(),
      category,
      priceCents,
      sellingUnit,
      images,
      startingQuantity: isCreating ? quantity : undefined,
    });
  };

  return (
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <View style={styles.field}>
        <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Photos</Text>
        <ProductPhotosField localImageUris={images} onChange={setImages} tier="FREE" />
      </View>

      <View style={styles.field}>
        <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Product name</Text>
        <TextInput
          value={name}
          onChangeText={setName}
          placeholder="Coca-Cola 500ml"
          placeholderTextColor={theme.colors.onSurfaceVariant}
          style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
          accessibilityLabel="Product name"
        />
        {fieldErrors.name && <Text style={[styles.error, { color: theme.colors.error }]}>{fieldErrors.name}</Text>}
      </View>

      <SelectFieldRow
        label="Category"
        valueLabel={labelFor(CATEGORY_OPTIONS, category)}
        onPress={() => setCategoryPickerOpen(true)}
      />

      <View style={styles.field}>
        <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Price</Text>
        <TextInput
          value={priceText}
          onChangeText={setPriceText}
          placeholder="R 12.00"
          placeholderTextColor={theme.colors.onSurfaceVariant}
          keyboardType="decimal-pad"
          style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
          accessibilityLabel="Price"
        />
        {priceText.length > 0 && priceCents !== null && (
          <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>{formatCents(priceCents)}</Text>
        )}
        {fieldErrors.priceCents && (
          <Text style={[styles.error, { color: theme.colors.error }]}>{fieldErrors.priceCents}</Text>
        )}
      </View>

      <SelectFieldRow
        label="Sold as"
        valueLabel={labelFor(UNIT_OPTIONS, sellingUnit)}
        onPress={() => setUnitPickerOpen(true)}
      />

      {isCreating && (
        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Starting quantity</Text>
          <TextInput
            value={quantityText}
            onChangeText={setQuantityText}
            placeholder="0"
            placeholderTextColor={theme.colors.onSurfaceVariant}
            keyboardType="number-pad"
            style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            accessibilityLabel="Starting quantity"
          />
          <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>
            Leave blank to start at 0 -- you can add stock any time from Inventory.
          </Text>
        </View>
      )}

      {submitError && <Text style={[styles.error, { color: theme.colors.error }]}>{submitError}</Text>}

      <Pressable
        onPress={handleSubmit}
        disabled={!canSubmit}
        style={({ pressed }) => [
          styles.submit,
          { backgroundColor: canSubmit ? theme.colors.primary : theme.colors.surfaceDisabled },
          pressed && canSubmit && styles.pressed,
        ]}
        accessibilityRole="button"
        accessibilityState={{ disabled: !canSubmit }}
        accessibilityLabel={submitLabel}
      >
        {isSubmitting ? (
          <ActivityIndicator color={theme.colors.onPrimary} />
        ) : (
          <Text
            style={[styles.submitText, { color: canSubmit ? theme.colors.onPrimary : theme.colors.onSurfaceDisabled }]}
          >
            {submitLabel}
          </Text>
        )}
      </Pressable>

      <SelectFieldModal
        visible={categoryPickerOpen}
        title="Select Category"
        options={CATEGORY_OPTIONS}
        selectedValue={category}
        onSelect={setCategory}
        onClose={() => setCategoryPickerOpen(false)}
      />
      <SelectFieldModal
        visible={unitPickerOpen}
        title="Select Unit"
        options={UNIT_OPTIONS}
        selectedValue={sellingUnit}
        onSelect={setSellingUnit}
        onClose={() => setUnitPickerOpen(false)}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.lg },
  field: { gap: spacing.sm },
  label: { ...typography.bodySmall },
  input: { borderWidth: 1, borderRadius: radius.md, paddingHorizontal: spacing.md, minHeight: 48, ...typography.body },
  hint: { ...typography.caption },
  error: { ...typography.bodySmall },
  submit: { minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radius.md },
  submitText: { ...typography.h2 },
  pressed: { opacity: 0.8 },
});
