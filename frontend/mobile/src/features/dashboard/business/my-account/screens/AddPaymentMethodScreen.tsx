import React, { useState } from "react";
import { ScrollView, StyleSheet, Text } from "react-native";
import { useRouter } from "expo-router";
import { TextInput, useTheme } from "react-native-paper";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { Note } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { usePaymentMethods } from "../hooks/usePaymentMethods";

/**
 * EFT only — Cash is created automatically and can't be removed (see
 * accountService.ts's seed); Card/gateway is a future integration with
 * its own Coming Soon row on Payment Methods, not something you "add"
 * here. file.txt §11: never a card number/CVV/PIN field anywhere on
 * this screen, by construction — there simply isn't one.
 * `accountNumber` is masked BEFORE it's ever passed to the service, so
 * nothing resembling a full account number exists in memory past this
 * function.
 */
export default function AddPaymentMethodScreen() {
  const router = useRouter();
  const theme = useTheme();
  const { addPaymentMethod, isAdding } = usePaymentMethods();

  const [bankName, setBankName] = useState("");
  const [accountNumber, setAccountNumber] = useState("");
  const [error, setError] = useState<string | null>(null);

  const canSubmit = bankName.trim().length > 0 && accountNumber.trim().length >= 4 && !isAdding;

  const handleSubmit = async () => {
    setError(null);
    try {
      const masked = `•••• ${accountNumber.trim().slice(-4)}`;
      await addPaymentMethod({
        type: "EFT",
        provider: bankName.trim(),
        maskedReference: masked,
        displayLabel: bankName.trim(),
      });
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't add that bank account. Try again.");
    }
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <TextInput
          mode="outlined"
          label="Bank name"
          placeholder="e.g. FNB, Capitec, Standard Bank"
          value={bankName}
          onChangeText={setBankName}
          autoFocus
        />
        <TextInput
          mode="outlined"
          label="Account number"
          value={accountNumber}
          onChangeText={setAccountNumber}
          keyboardType="numeric"
        />
        {error && <Text style={[styles.error, { color: theme.colors.error }]}>{error}</Text>}
        <PrimaryButton onPress={handleSubmit} loading={isAdding} disabled={!canSubmit}>
          Add bank account
        </PrimaryButton>
        <Note>
          Only the last 4 digits are kept, for display. TruConnect never stores full account numbers, card numbers,
          PINs, or CVVs. New EFT accounts start as pending until verified — EFT leaves a real digital banking
          trail, which is what makes it useful for larger supplier payments.
        </Note>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.md },
  error: { ...typography.bodySmall },
});
