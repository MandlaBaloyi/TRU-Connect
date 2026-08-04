/**
 * RecordSaleScreen — the ≤30-second flow (Doc 06 §12.1). Theme-aware.
 */

import React, { useMemo, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { useLoanPayments, useLoanSearch } from "../hooks";
import { parseRandsToCents } from "../services/loanMapper";
import { validateAmount, validateCustomerName } from "../services/loanValidation";
import { CustomerAvatar, LoanSearchBar } from "../components";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";

/** All this screen ever needs from a chosen customer — deliberately
 *  narrower than the full Customer type, so a pre-filled selection
 *  arriving as route params (id + name only, see below) doesn't need to
 *  fabricate fields like firstRecordedAt just to satisfy the shape. */
interface SelectedCustomer {
  id: string;
  name: string;
}

export default function RecordSaleScreen() {
  const router = useRouter();
  const theme = useTheme();
  const { recordSale, isRecordingSale } = useLoanPayments();
  const search = useLoanSearch();

  // PRE-FILL: when arriving from CustomerLoansScreen's "Record another
  // sale", customerId/customerName are passed as route params — the
  // owner is already looking at that customer's account, so re-searching
  // for them here would be pure friction (Doc 02 §1.2). Read once on
  // mount via a lazy initializer rather than an effect, since there is
  // nothing to react to afterward — the params don't change mid-screen.
  const { customerId: prefillId, customerName: prefillName } = useLocalSearchParams<{
    customerId?: string;
    customerName?: string;
  }>();

  const [selectedCustomer, setSelectedCustomer] = useState<SelectedCustomer | undefined>(() =>
    prefillId && prefillName ? { id: prefillId, name: prefillName } : undefined
  );
  const [newCustomerName, setNewCustomerName] = useState("");
  const [newCustomerPhone, setNewCustomerPhone] = useState("");
  const [amountText, setAmountText] = useState("");
  const [description, setDescription] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);

  const amountCents = useMemo(() => parseRandsToCents(amountText), [amountText]);
  const amountError = amountText.length > 0 ? validateAmount(amountCents ?? undefined) : null;

  const isCreatingNew = !selectedCustomer && search.term.trim().length > 0 && !search.hasResults;
  const nameError =
    isCreatingNew && newCustomerName.length > 0 ? validateCustomerName(newCustomerName) : null;

  const hasCustomer = Boolean(selectedCustomer) || newCustomerName.trim().length >= 2;
  const canSubmit =
    hasCustomer && amountCents !== null && amountError === null && !nameError && !isRecordingSale;

  const handleSubmit = async () => {
    if (!canSubmit || amountCents === null) return;
    setSubmitError(null);
    try {
      await recordSale({
        customerId: selectedCustomer?.id,
        newCustomerName: selectedCustomer ? undefined : newCustomerName.trim(),
        newCustomerPhone: selectedCustomer ? undefined : newCustomerPhone.trim() || undefined,
        amount: amountCents,
        description: description.trim() || undefined,
      });
      router.back();
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : "Could not record that sale. Try again."
      );
    }
  };

  return (
    <ScreenContainer>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {selectedCustomer ? (
          <Pressable
            style={[styles.selectedCustomer, { backgroundColor: theme.colors.surfaceVariant }]}
            onPress={() => {
              setSelectedCustomer(undefined);
              search.setTerm("");
            }}
            accessibilityRole="button"
            accessibilityLabel={`${selectedCustomer.name} selected. Tap to change.`}
          >
            <CustomerAvatar name={selectedCustomer.name} seed={selectedCustomer.id} />
            <View style={styles.selectedText}>
              <Text style={[styles.selectedName, { color: theme.colors.onSurface }]}>
                {selectedCustomer.name}
              </Text>
              <Text style={[styles.changeHint, { color: theme.colors.onSurfaceVariant }]}>
                Tap to change
              </Text>
            </View>
          </Pressable>
        ) : (
          <View style={styles.field}>
            <LoanSearchBar
              value={search.term}
              onChangeText={(text) => {
                search.setTerm(text);
                setNewCustomerName(text);
              }}
              onClear={() => {
                search.clear();
                setNewCustomerName("");
              }}
              label="Who is buying?"
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
                    <Text style={[styles.resultName, { color: theme.colors.onSurface }]}>
                      {customer.name}
                    </Text>
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

        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>How much do they owe?</Text>
          <View style={[styles.amountInputRow, { borderColor: theme.colors.outline }]}>
            <Text style={[styles.currency, { color: theme.colors.onSurfaceVariant }]}>R</Text>
            <TextInput
              value={amountText}
              onChangeText={(text) => {
                setAmountText(text);
                setSubmitError(null);
              }}
              keyboardType="decimal-pad"
              placeholder="0.00"
              placeholderTextColor={theme.colors.onSurfaceVariant}
              style={[styles.amountInput, { color: theme.colors.onSurface }]}
              accessibilityLabel="Amount owed in rands"
            />
          </View>
          {amountError && <Text style={[styles.error, { color: theme.colors.error }]}>{amountError}</Text>}
        </View>

        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>What for? (optional)</Text>
          <TextInput
            value={description}
            onChangeText={setDescription}
            placeholder="Groceries"
            placeholderTextColor={theme.colors.onSurfaceVariant}
            style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            accessibilityLabel="What the sale was for, optional"
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
          accessibilityLabel="Save this credit sale"
        >
          {isRecordingSale ? (
            <ActivityIndicator color={theme.colors.onSecondary} />
          ) : (
            <Text
              style={[
                styles.submitText,
                { color: canSubmit ? theme.colors.onSecondary : theme.colors.onSurfaceDisabled },
              ]}
            >
              Save
            </Text>
          )}
        </Pressable>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.lg },
  field: { gap: spacing.sm },
  label: { ...typography.bodySmall },
  selectedCustomer: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    borderRadius: radius.md,
    padding: spacing.md,
    minHeight: 44,
  },
  selectedText: { flex: 1 },
  selectedName: { ...typography.h2 },
  changeHint: { ...typography.caption },
  results: { borderWidth: 1, borderRadius: radius.md, overflow: "hidden" },
  resultRow: { flexDirection: "row", alignItems: "center", gap: spacing.md, padding: spacing.md, minHeight: 44 },
  resultName: { ...typography.body },
  newCustomer: { gap: spacing.sm },
  newCustomerLabel: { ...typography.bodySmall },
  input: {
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    minHeight: 48,
    ...typography.body,
  },
  amountInputRow: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    minHeight: 56,
    gap: spacing.sm,
  },
  currency: { ...typography.h1 },
  amountInput: { flex: 1, ...typography.h1 },
  error: { ...typography.bodySmall },
  submit: { minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radius.md },
  submitText: { ...typography.h2 },
  pressed: { opacity: 0.8 },
});
