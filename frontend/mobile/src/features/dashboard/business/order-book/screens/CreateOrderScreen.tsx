/**
 * CreateOrderScreen — record an order in one screen, no wizard steps.
 * Customer step mirrors RecordSaleScreen exactly: search existing
 * customer, select, or fall through to inline new-customer creation —
 * "adding a customer must never be a separate screen" applies here too.
 */

import React, { useMemo, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Plus } from "lucide-react-native";

import { useOrderCustomerSearch, useOrderMutations } from "../hooks";
import { calculateLineTotal, formatCents, parseRandsToCents } from "../services/orderMapper";
import {
  validateCustomerName,
  validateLineItemDescription,
  validateQuantity,
  validateUnitPrice,
} from "../services/orderValidation";
import { CustomerAvatar, OrderSearchBar } from "../components";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";

interface SelectedCustomer {
  id: string;
  name: string;
}

interface DraftLineItem {
  id: string;
  description: string;
  quantityText: string;
  priceText: string;
}

function newDraftItem(): DraftLineItem {
  return { id: `draft-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, description: "", quantityText: "1", priceText: "" };
}

export default function CreateOrderScreen() {
  const router = useRouter();
  const theme = useTheme();
  const { createOrder, isCreatingOrder } = useOrderMutations();
  const search = useOrderCustomerSearch();

  const [selectedCustomer, setSelectedCustomer] = useState<SelectedCustomer | undefined>(undefined);
  const [newCustomerName, setNewCustomerName] = useState("");
  const [newCustomerPhone, setNewCustomerPhone] = useState("");
  const [items, setItems] = useState<DraftLineItem[]>([newDraftItem()]);
  const [notes, setNotes] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);

  const isCreatingNew = !selectedCustomer && search.term.trim().length > 0 && !search.hasResults;
  const nameError = isCreatingNew && newCustomerName.length > 0 ? validateCustomerName(newCustomerName) : null;
  const hasCustomer = Boolean(selectedCustomer) || newCustomerName.trim().length >= 2;

  const parsedItems = useMemo(
    () =>
      items.map((item) => {
        const quantity = item.quantityText.trim().length > 0 ? Number.parseInt(item.quantityText, 10) : null;
        const unitPrice = parseRandsToCents(item.priceText);
        return {
          ...item,
          quantity,
          unitPrice,
          quantityError: validateQuantity(quantity),
          priceError: item.priceText.length > 0 ? validateUnitPrice(unitPrice) : "Enter a price.",
          descriptionError: validateLineItemDescription(item.description),
        };
      }),
    [items]
  );

  const validItems = parsedItems.filter(
    (item) => !item.descriptionError && !item.quantityError && !item.priceError && item.quantity && item.unitPrice !== null
  );
  const runningTotal = validItems.reduce(
    (sum, item) => sum + calculateLineTotal(item.quantity as number, item.unitPrice as number),
    0
  );
  const hasAnyContent = items.some((item) => item.description.trim().length > 0);
  const allFilledItemsValid = parsedItems
    .filter((item) => item.description.trim().length > 0)
    .every((item) => !item.descriptionError && !item.quantityError && !item.priceError);

  const canSubmit =
    hasCustomer &&
    hasAnyContent &&
    allFilledItemsValid &&
    validItems.length > 0 &&
    !isCreatingOrder;

  const updateItem = (id: string, patch: Partial<DraftLineItem>) => {
    setItems((current) => current.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  };
  const removeItem = (id: string) => {
    setItems((current) => (current.length > 1 ? current.filter((item) => item.id !== id) : current));
  };
  const addItem = () => setItems((current) => [...current, newDraftItem()]);

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setSubmitError(null);
    try {
      await createOrder({
        customerId: selectedCustomer?.id,
        newCustomerName: selectedCustomer ? undefined : newCustomerName.trim(),
        newCustomerPhone: selectedCustomer ? undefined : newCustomerPhone.trim() || undefined,
        items: validItems.map((item) => ({
          description: item.description.trim(),
          quantity: item.quantity as number,
          unitPrice: item.unitPrice as number,
        })),
        notes: notes.trim() || undefined,
      });
      router.back();
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Could not record that order. Try again.");
    }
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {/* Customer */}
        {selectedCustomer ? (
          <Pressable
            style={[styles.selectedCustomer, { backgroundColor: theme.colors.surfaceVariant }]}
            onPress={() => {
              setSelectedCustomer(undefined);
              search.clear();
            }}
            accessibilityRole="button"
            accessibilityLabel={`${selectedCustomer.name} selected. Tap to change.`}
          >
            <CustomerAvatar name={selectedCustomer.name} seed={selectedCustomer.id} />
            <View style={styles.selectedText}>
              <Text style={[styles.selectedName, { color: theme.colors.onSurface }]}>{selectedCustomer.name}</Text>
              <Text style={[styles.changeHint, { color: theme.colors.onSurfaceVariant }]}>Tap to change</Text>
            </View>
          </Pressable>
        ) : (
          <View style={styles.field}>
            <OrderSearchBar
              value={search.term}
              onChangeText={(text) => {
                search.setTerm(text);
                setNewCustomerName(text);
              }}
              onClear={() => {
                search.clear();
                setNewCustomerName("");
              }}
              label="Who is this order for?"
              placeholder="Search by name or phone"
            />

            {search.hasResults && (
              <View style={[styles.results, { borderColor: theme.colors.outline }]}>
                {search.results.slice(0, 5).map((customer) => (
                  <Pressable
                    key={customer.id}
                    style={styles.resultRow}
                    onPress={() => setSelectedCustomer(customer)}
                    accessibilityRole="button"
                    accessibilityLabel={`Select ${customer.name}`}
                  >
                    <CustomerAvatar name={customer.name} seed={customer.id} size={36} />
                    <Text style={[styles.resultName, { color: theme.colors.onSurface }]}>{customer.name}</Text>
                  </Pressable>
                ))}
              </View>
            )}

            {isCreatingNew && (
              <View style={styles.newCustomer}>
                <Text style={[styles.newCustomerLabel, { color: theme.colors.secondary }]}>
                  New customer: {newCustomerName.trim()}
                </Text>
                {nameError && <Text style={[styles.error, { color: theme.colors.error }]}>{nameError}</Text>}
                <TextInput
                  value={newCustomerPhone}
                  onChangeText={setNewCustomerPhone}
                  placeholder="Phone number (optional)"
                  placeholderTextColor={theme.colors.onSurfaceVariant}
                  keyboardType="phone-pad"
                  style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
                  accessibilityLabel="Customer phone number, optional"
                />
              </View>
            )}
          </View>
        )}

        {/* Order card — items live in one card, not floating separately */}
        <View style={[styles.orderCard, { borderColor: theme.colors.outline }]}>
          <View style={styles.field}>
            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Items</Text>
            {parsedItems.map((item) => (
            <View key={item.id} style={[styles.itemBlock, { borderColor: theme.colors.outline }]}>
              <View style={styles.itemRow}>
                <TextInput
                  value={item.description}
                  onChangeText={(text) => updateItem(item.id, { description: text })}
                  placeholder="e.g. Big Kota"
                  placeholderTextColor={theme.colors.onSurfaceVariant}
                  style={[styles.itemDescriptionInput, { color: theme.colors.onSurface }]}
                  accessibilityLabel="Item description"
                />
                {items.length > 1 && (
                  <Pressable onPress={() => removeItem(item.id)} hitSlop={12} accessibilityRole="button" accessibilityLabel="Remove item">
                    <Text style={{ color: theme.colors.error, fontSize: 15 }}>✕</Text>
                  </Pressable>
                )}
              </View>
              <View style={styles.itemRow}>
                <TextInput
                  value={item.quantityText}
                  onChangeText={(text) => updateItem(item.id, { quantityText: text })}
                  placeholder="Qty"
                  keyboardType="number-pad"
                  placeholderTextColor={theme.colors.onSurfaceVariant}
                  style={[styles.itemQtyInput, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
                  accessibilityLabel="Quantity"
                />
                <View style={[styles.itemPriceRow, { borderColor: theme.colors.outline }]}>
                  <Text style={{ color: theme.colors.onSurfaceVariant }}>R</Text>
                  <TextInput
                    value={item.priceText}
                    onChangeText={(text) => updateItem(item.id, { priceText: text })}
                    placeholder="0.00"
                    keyboardType="decimal-pad"
                    placeholderTextColor={theme.colors.onSurfaceVariant}
                    style={[styles.itemPriceInput, { color: theme.colors.onSurface }]}
                    accessibilityLabel="Unit price in rands"
                  />
                </View>
              </View>
              {item.description.trim().length > 0 && (item.quantityError || item.priceError) && (
                <Text style={[styles.error, { color: theme.colors.error }]}>
                  {item.quantityError ?? item.priceError}
                </Text>
              )}
            </View>
          ))}

          <Pressable onPress={addItem} style={styles.addItemButton} accessibilityRole="button" accessibilityLabel="Add another item">
            <Plus size={16} color={theme.colors.primary} />
            <Text style={[styles.addItemText, { color: theme.colors.primary }]}>Add item</Text>
          </Pressable>
          </View>

          {validItems.length > 0 && (
            <View style={[styles.totalRow, { borderTopColor: theme.colors.outline }]}>
              <Text style={[styles.totalLabel, { color: theme.colors.onSurfaceVariant }]}>Total</Text>
              <Text style={[styles.totalValue, { color: theme.colors.onSurface }]}>{formatCents(runningTotal)}</Text>
            </View>
          )}
        </View>

        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Notes (optional)</Text>
          <TextInput
            value={notes}
            onChangeText={setNotes}
            placeholder="Collecting after 5pm"
            placeholderTextColor={theme.colors.onSurfaceVariant}
            style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            accessibilityLabel="Order notes, optional"
          />
        </View>

        {submitError && <Text style={[styles.error, { color: theme.colors.error }]}>{submitError}</Text>}

        <Pressable
          onPress={handleSubmit}
          disabled={!canSubmit}
          style={({ pressed }) => [
            styles.submit,
            { backgroundColor: canSubmit ? theme.colors.secondary : theme.colors.surfaceDisabled },
            pressed && canSubmit && styles.pressed,
          ]}
          accessibilityRole="button"
          accessibilityState={{ disabled: !canSubmit }}
          accessibilityLabel="Save this order"
        >
          {isCreatingOrder ? (
            <ActivityIndicator color={theme.colors.onSecondary} />
          ) : (
            <Text style={[styles.submitText, { color: canSubmit ? theme.colors.onSecondary : theme.colors.onSurfaceDisabled }]}>
              Save order
            </Text>
          )}
        </Pressable>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.lg },
  orderCard: { borderWidth: 1, borderRadius: radius.md, padding: spacing.md, gap: spacing.md },
  field: { gap: spacing.sm },
  label: { ...typography.bodySmall },
  selectedCustomer: { flexDirection: "row", alignItems: "center", gap: spacing.md, borderRadius: radius.md, padding: spacing.md, minHeight: 44 },
  selectedText: { flex: 1 },
  selectedName: { ...typography.h2 },
  changeHint: { ...typography.caption },
  results: { borderWidth: 1, borderRadius: radius.md, overflow: "hidden" },
  resultRow: { flexDirection: "row", alignItems: "center", gap: spacing.md, padding: spacing.md, minHeight: 44 },
  resultName: { ...typography.body },
  newCustomer: { gap: spacing.sm },
  newCustomerLabel: { ...typography.bodySmall },
  input: { borderWidth: 1, borderRadius: radius.md, paddingHorizontal: spacing.md, minHeight: 48, ...typography.body },
  itemBlock: { borderWidth: 1, borderRadius: radius.md, padding: spacing.sm, gap: spacing.sm },
  itemRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  itemDescriptionInput: { flex: 1, ...typography.body, minHeight: 40 },
  itemQtyInput: { width: 64, borderWidth: 1, borderRadius: radius.sm, paddingHorizontal: spacing.sm, minHeight: 40, ...typography.body },
  itemPriceRow: { flex: 1, flexDirection: "row", alignItems: "center", gap: spacing.xs, borderWidth: 1, borderRadius: radius.sm, paddingHorizontal: spacing.sm, minHeight: 40 },
  itemPriceInput: { flex: 1, ...typography.body },
  addItemButton: { flexDirection: "row", alignItems: "center", gap: spacing.xs, minHeight: 40, paddingVertical: spacing.xs },
  addItemText: { ...typography.body, fontWeight: "600" },
  totalRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", borderTopWidth: StyleSheet.hairlineWidth, paddingTop: spacing.sm },
  totalLabel: { ...typography.body },
  totalValue: { ...typography.h1, fontWeight: "700" },
  error: { ...typography.bodySmall },
  submit: { minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radius.md },
  submitText: { ...typography.h2 },
  pressed: { opacity: 0.8 },
});
