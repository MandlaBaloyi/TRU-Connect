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
import { stripEmoji } from "../algorithms/textSanitizers";
import { ProductPhotosField } from "./ProductPhotosField";
import { SelectFieldModal } from "./SelectFieldModal";
import { SelectFieldRow } from "./SelectFieldRow";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

export interface ProductFormValues {
  name: string;
  category: ProductCategory;
  priceCents: Cents;
  /** The "was RX" comparison price for a sale/promotion -- undefined
   *  when not running one. Validated (must be higher than priceCents)
   *  the same way on both mock and http (see productMapper.ts's own
   *  parseCentsInput, shared with the real price field). */
  compareAtPriceCents?: Cents;
  sellingUnit: ProductUnit;
  /** WHAT IS INSIDE the unit -- "Case" + 6 + "Bottle" reads as "Case
   *  of 6 bottles", and is what makes a per-unit price computable.
   *  Both optional and only meaningful together: plenty of products
   *  are genuinely just sold as Each.
   *
   *  Both columns have existed on Product from the start; this form
   *  never collected them, so every catalogue said "Case" and never
   *  "case of what". See the note beside their state in this file. */
  unitQuantity?: number;
  unitMeasure?: ProductUnit;
  /** Plain text, optional. */
  description?: string;
  /** Optional to type -- left blank, the backend auto-generates a
   *  stable one. Editable on BOTH create and edit, unlike productCode
   *  (never shown on this form at all -- see Product.productCode's
   *  own docstring in types.ts; it doesn't exist yet at creation time,
   *  and is never editable once it does). */
  sku?: string;
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
  const [description, setDescription] = useState(initialValues?.description ?? "");
  const [category, setCategory] = useState<ProductCategory>(initialValues?.category ?? "OTHER");
  const [categoryPickerOpen, setCategoryPickerOpen] = useState(false);
  const [priceText, setPriceText] = useState(
    initialValues?.priceCents !== undefined ? String(initialValues.priceCents / 100) : ""
  );
  const [compareAtPriceText, setCompareAtPriceText] = useState(
    initialValues?.compareAtPriceCents !== undefined ? String(initialValues.compareAtPriceCents / 100) : ""
  );
  const [sellingUnit, setSellingUnit] = useState<ProductUnit>(initialValues?.sellingUnit ?? "EACH");
  const [unitPickerOpen, setUnitPickerOpen] = useState(false);
  // WHAT IS ACTUALLY IN THE PACK. Both columns have existed on Product
  // since the beginning and NOTHING has ever let a supplier fill them
  // in -- so every product in the catalogue said "Case" and never
  // "case of what, how many". Everything downstream was already built
  // and silently dark: unitEconomics computes a per-unit price from
  // these, the business-facing DTO ships them, the product screen
  // renders "Case of 6 bottles", and the storefront's whole
  // better-per-unit section queries them. This form was the missing
  // link, found while trying to test that section.
  const [unitQuantityText, setUnitQuantityText] = useState(
    initialValues?.unitQuantity != null ? String(initialValues.unitQuantity) : ""
  );
  const [unitMeasure, setUnitMeasure] = useState<ProductUnit | null>(
    initialValues?.unitMeasure ?? null
  );
  const [measurePickerOpen, setMeasurePickerOpen] = useState(false);
  const [quantityText, setQuantityText] = useState("");
  const [sku, setSku] = useState(initialValues?.sku ?? "");

  const priceCents = parseCentsInput(priceText);
  // Blank is genuinely valid (no sale running) -- only parsed/validated
  // once something's actually been typed.
  const compareAtPriceCents = compareAtPriceText.trim() === "" ? undefined : parseCentsInput(compareAtPriceText) ?? undefined;
  const compareAtPriceTouchedButInvalid = compareAtPriceText.trim() !== "" && compareAtPriceCents === undefined;
  // REAL GAP FOUND DURING REVIEW: a technically-valid number (e.g. 300
  // when price is 320) was never checked against price on THIS form at
  // all -- it only ever got caught after a full round trip to the
  // server. Same rule as product_service.py's own validation, checked
  // here too so a supplier sees the problem immediately.
  const compareAtPriceNotHigherThanPrice =
    compareAtPriceCents !== undefined && priceCents !== null && compareAtPriceCents <= priceCents;
  // Blank is a real answer -- plenty of products are just sold as
  // Each, and a pack size is never required.
  const unitQuantity =
    unitQuantityText.trim() === "" ? null : Number.parseInt(unitQuantityText, 10);
  const unitQuantityInvalid =
    unitQuantityText.trim() !== "" && (!Number.isFinite(unitQuantity) || (unitQuantity ?? 0) < 1);

  const quantity = quantityText.trim() === "" ? 0 : Number.parseInt(quantityText, 10);
  const isValidQuantity = Number.isFinite(quantity) && quantity >= 0;
  const canSubmit =
    name.trim().length > 0 &&
    priceCents !== null &&
    !compareAtPriceTouchedButInvalid &&
    !compareAtPriceNotHigherThanPrice &&
    !unitQuantityInvalid &&
    (!isCreating || isValidQuantity) &&
    !isSubmitting;

  const handleSubmit = () => {
    if (
      priceCents === null ||
      compareAtPriceTouchedButInvalid ||
      compareAtPriceNotHigherThanPrice ||
      unitQuantityInvalid ||
      (isCreating && !isValidQuantity)
    )
      return;
    onSubmit({
      name: name.trim(),
      category,
      priceCents,
      compareAtPriceCents,
      sellingUnit,
      // Only meaningful together: a quantity with no measure is "Case
      // of 6" (fine), a measure with no quantity says nothing at all.
      unitQuantity: unitQuantity ?? undefined,
      unitMeasure: unitQuantity ? (unitMeasure ?? undefined) : undefined,
      description: description.trim() || undefined,
      sku: sku.trim() || undefined,
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
          onChangeText={(text) => setName(stripEmoji(text))}
          placeholder="Coca-Cola 500ml"
          placeholderTextColor={theme.colors.onSurfaceVariant}
          style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
          accessibilityLabel="Product name"
        />
        {fieldErrors.name && <Text style={[styles.error, { color: theme.colors.error }]}>{fieldErrors.name}</Text>}
      </View>

      <View style={styles.field}>
        <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Description (optional)</Text>
        <TextInput
          value={description}
          onChangeText={setDescription}
          placeholder="e.g. 3 loaves per case."
          placeholderTextColor={theme.colors.onSurfaceVariant}
          multiline
          numberOfLines={8}
          style={[
            styles.input,
            styles.multilineInput,
            { borderColor: theme.colors.outline, color: theme.colors.onSurface },
          ]}
          accessibilityLabel="Description"
        />
        {fieldErrors.description && (
          <Text style={[styles.error, { color: theme.colors.error }]}>{fieldErrors.description}</Text>
        )}
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

      <View style={styles.field}>
        <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Compare-at price (optional)</Text>
        <TextInput
          value={compareAtPriceText}
          onChangeText={setCompareAtPriceText}
          placeholder={'e.g. R 25.00 -- shown crossed out as "was RX"'}
          placeholderTextColor={theme.colors.onSurfaceVariant}
          keyboardType="decimal-pad"
          style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
          accessibilityLabel="Compare-at price"
        />
        {compareAtPriceText.length > 0 && compareAtPriceCents !== undefined && (
          <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>{formatCents(compareAtPriceCents)}</Text>
        )}
        {compareAtPriceTouchedButInvalid && !fieldErrors.compareAtPriceCents && (
          <Text style={[styles.error, { color: theme.colors.error }]}>Enter a valid amount.</Text>
        )}
        {compareAtPriceNotHigherThanPrice && !fieldErrors.compareAtPriceCents && (
          <Text style={[styles.error, { color: theme.colors.error }]}>
            Compare-at price must be higher than the actual price to show as a discount.
          </Text>
        )}
        {fieldErrors.compareAtPriceCents && (
          <Text style={[styles.error, { color: theme.colors.error }]}>{fieldErrors.compareAtPriceCents}</Text>
        )}
      </View>

      <SelectFieldRow
        label="Sold as"
        valueLabel={labelFor(UNIT_OPTIONS, sellingUnit)}
        onPress={() => setUnitPickerOpen(true)}
      />

      {/* WHAT IS IN THE PACK. Hidden for a product sold as Each,
          because "Each of 6" is nonsense -- there is nothing inside a
          single item to count. Optional even when shown: a supplier
          who does not know or does not care leaves it blank and
          nothing downstream claims otherwise. */}
      {sellingUnit !== "EACH" && (
        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>
            What is in the {labelFor(UNIT_OPTIONS, sellingUnit).toLowerCase()}? (optional)
          </Text>
          <View style={styles.packRow}>
            <TextInput
              value={unitQuantityText}
              onChangeText={setUnitQuantityText}
              keyboardType="number-pad"
              placeholder="6"
              style={[styles.input, styles.packQuantity, { color: theme.colors.onSurface, borderColor: theme.colors.outline }]}
              placeholderTextColor={theme.colors.onSurfaceVariant}
            />
            <Pressable
              onPress={() => setMeasurePickerOpen(true)}
              style={[styles.input, styles.packMeasure, { borderColor: theme.colors.outline }]}
              accessibilityRole="button"
              accessibilityLabel="Choose what is in the pack"
            >
              <Text style={{ color: unitMeasure ? theme.colors.onSurface : theme.colors.onSurfaceVariant }}>
                {unitMeasure ? labelFor(UNIT_OPTIONS, unitMeasure) : "Bottles, cans…"}
              </Text>
            </Pressable>
          </View>
          {unitQuantityInvalid ? (
            <Text style={[styles.error, { color: theme.colors.error }]}>
              Enter how many are in the pack, or leave it blank.
            </Text>
          ) : (
            <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>
              Lets businesses see the price per item — the number they compare suppliers on.
            </Text>
          )}
        </View>
      )}

      <View style={styles.field}>
        <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>SKU (optional)</Text>
        <TextInput
          value={sku}
          onChangeText={(text) => setSku(stripEmoji(text))}
          placeholder="Leave blank to auto-generate"
          placeholderTextColor={theme.colors.onSurfaceVariant}
          autoCapitalize="characters"
          style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
          accessibilityLabel="SKU"
        />
        <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>
          Your own tracking label -- used to see which products sell the most. Leave blank and we'll generate one for
          you.
        </Text>
        {fieldErrors.sku && <Text style={[styles.error, { color: theme.colors.error }]}>{fieldErrors.sku}</Text>}
      </View>

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
      {/* SAME UNIT VOCABULARY AS "Sold as", deliberately -- a Case of
          6 Bottles uses one list for both halves, so there is no
          second set of words to keep in step. */}
      <SelectFieldModal
        visible={measurePickerOpen}
        title="What is inside?"
        options={UNIT_OPTIONS}
        selectedValue={unitMeasure ?? "EACH"}
        onSelect={setUnitMeasure}
        onClose={() => setMeasurePickerOpen(false)}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.lg },
  field: { gap: spacing.sm },
  packRow: { flexDirection: "row", gap: spacing.sm },
  packQuantity: { width: 92, textAlign: "center" },
  packMeasure: { flex: 1, justifyContent: "center" },
  label: { ...typography.bodySmall },
  input: { borderWidth: 1, borderRadius: radius.md, paddingHorizontal: spacing.md, minHeight: 48, ...typography.body },
  multilineInput: { paddingTop: spacing.sm, textAlignVertical: "top", minHeight: 140 },
  hint: { ...typography.caption },
  error: { ...typography.bodySmall },
  submit: { minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radius.md },
  submitText: { ...typography.h2 },
  pressed: { opacity: 0.8 },
});
