/**
 * AddPaymentScreen — the ≤15-second flow. Theme-aware.
 */

import React, { useMemo, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import { useCustomer, useLoan, useLoanPayments } from "../hooks";
import { formatCents, parseRandsToCents } from "../services/loanMapper";
import { suggestQuickAmounts, validatePayment, willSettleEntry } from "../algorithms/paymentAllocation";
import { QuickAmountRow } from "../components";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";

export default function AddPaymentScreen() {
  const router = useRouter();
  const theme = useTheme();
  const { loanId } = useLocalSearchParams<{ loanId: string }>();
  const { loan, isLoading, notFound } = useLoan(loanId ?? "");
  const { customer } = useCustomer(loan?.entry.customerId ?? "");
  const { recordPayment, isRecordingPayment } = useLoanPayments();

  const [amountText, setAmountText] = useState("");
  const [selectedQuick, setSelectedQuick] = useState<number | undefined>();
  const [note, setNote] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);

  const amountCents = useMemo(() => parseRandsToCents(amountText), [amountText]);

  const quickAmounts = useMemo(
    () => (loan ? suggestQuickAmounts(loan.outstandingAmount) : []),
    [loan]
  );

  const validation = useMemo(() => {
    if (!loan || amountCents === null) return null;
    return validatePayment(loan.entry, loan.payments, amountCents);
  }, [loan, amountCents]);

  const settles = useMemo(
    () => (loan && amountCents !== null ? willSettleEntry(loan.entry, loan.payments, amountCents) : false),
    [loan, amountCents]
  );

  if (isLoading) {
    return (
      <ScreenContainer>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (notFound || !loan) {
    return (
      <ScreenContainer>
        <ErrorState message="This purchase no longer exists. It may have been removed." />
      </ScreenContainer>
    );
  }

  const canSubmit = validation?.isValid === true && !isRecordingPayment;

  const handleQuickSelect = (amount: number) => {
    setSelectedQuick(amount);
    setAmountText((amount / 100).toFixed(2));
    setSubmitError(null);
  };

  const handleSubmit = async () => {
    if (amountCents === null || !canSubmit) return;
    setSubmitError(null);
    try {
      await recordPayment({
        loanEntryId: loan.entry.id,
        amount: amountCents,
        note: note.trim() || undefined,
      });
      router.back();
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : "Could not record that payment. Try again."
      );
    }
  };

  return (
    <ScreenContainer>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.summary}>
          <Text style={[styles.summaryLabel, { color: theme.colors.onSurfaceVariant }]}>
            {customer?.customer.name ?? "Customer"} still owes
          </Text>
          <Text style={[styles.summaryAmount, { color: theme.colors.onBackground }]}>
            {formatCents(loan.outstandingAmount)}
          </Text>
        </View>

        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Quick amounts</Text>
          <QuickAmountRow
            amounts={quickAmounts}
            selected={selectedQuick}
            outstanding={loan.outstandingAmount}
            onSelect={handleQuickSelect}
          />
        </View>

        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Or enter an amount</Text>
          <View style={[styles.amountInputRow, { borderColor: theme.colors.outline }]}>
            <Text style={[styles.currency, { color: theme.colors.onSurfaceVariant }]}>R</Text>
            <TextInput
              value={amountText}
              onChangeText={(text) => {
                setAmountText(text);
                setSelectedQuick(undefined);
                setSubmitError(null);
              }}
              keyboardType="decimal-pad"
              placeholder="0.00"
              placeholderTextColor={theme.colors.onSurfaceVariant}
              style={[styles.amountInput, { color: theme.colors.onSurface }]}
              accessibilityLabel="Payment amount in rands"
            />
          </View>
          {validation && !validation.isValid && (
            <Text style={[styles.error, { color: theme.colors.error }]}>{validation.message}</Text>
          )}
          {validation?.isValid && settles && (
            <Text style={[styles.settleHint, { color: theme.colors.secondary }]}>
              This settles the debt completely.
            </Text>
          )}
          {validation?.isValid && !settles && validation.resultingOutstanding !== undefined && (
            <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>
              {formatCents(validation.resultingOutstanding)} will still be owed.
            </Text>
          )}
        </View>

        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Note (optional)</Text>
          <TextInput
            value={note}
            onChangeText={setNote}
            placeholder="Part payment"
            placeholderTextColor={theme.colors.onSurfaceVariant}
            style={[styles.noteInput, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            accessibilityLabel="Payment note"
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
          accessibilityLabel="Save this payment"
        >
          {isRecordingPayment ? (
            <ActivityIndicator color={theme.colors.onSecondary} />
          ) : (
            <Text
              style={[
                styles.submitText,
                { color: canSubmit ? theme.colors.onSecondary : theme.colors.onSurfaceDisabled },
              ]}
            >
              Save payment
            </Text>
          )}
        </Pressable>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.lg },
  centre: { paddingVertical: spacing.xxl, alignItems: "center" },
  summary: { gap: spacing.xs },
  summaryLabel: { ...typography.body },
  summaryAmount: { ...typography.display },
  field: { gap: spacing.sm },
  label: { ...typography.bodySmall },
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
  noteInput: { borderWidth: 1, borderRadius: radius.md, paddingHorizontal: spacing.md, minHeight: 48, ...typography.body },
  error: { ...typography.bodySmall },
  hint: { ...typography.bodySmall },
  settleHint: { ...typography.bodySmall, fontWeight: "600" },
  submit: { minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radius.md },
  submitText: { ...typography.h2 },
  pressed: { opacity: 0.8 },
});
