import React, { useState } from "react";
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Check, CreditCard } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { DeliveryType, PaymentMethod } from "../types";

const DELIVERY_OPTIONS: { value: DeliveryType; label: string }[] = [
  { value: "DELIVER", label: "Deliver" },
  { value: "COLLECT", label: "Collect" },
];

const PAYMENT_OPTIONS: { value: PaymentMethod; label: string; description: string }[] = [
  { value: "CASH", label: "Cash", description: "Pay on delivery or collection" },
  { value: "PROOF_OF_PAYMENT", label: "Proof of Payment", description: "Pay the supplier directly, then send proof" },
];

const DEFAULT_ADDRESS_PLACEHOLDER = "Enter your delivery or collection address";

/**
 * Step 1 of 3 -- a real, full screen, not a bottom sheet. Confirmed
 * directly after review: this needs an address field too, which is a
 * lot to cram into a sheet, and it matches how the Bash reference
 * itself treats this step as its own screen.
 *
 * A REAL THIRD PAYMENT OPTION sits here -- "Pay Online (Card / Instant
 * EFT)". Named around what it DOES, not which processor sits behind
 * it, so the label stays correct even if the provider ever changes.
 * Tapping it shows "Coming soon" and never actually selects it --
 * the real backend already correctly rejects PAYFAST as unavailable,
 * so this is never even attempted.
 *
 * NO "Confirm Order" BUTTON HERE -- deliberately. This screen only
 * collects the delivery/payment choice; the real submission (and the
 * real "Confirm Order" button) live on the Review Order screen next,
 * after the business has seen everything together.
 */
export default function DeliveryPaymentScreen() {
  const { supplierId } = useLocalSearchParams<{ supplierId: string }>();
  const router = useRouter();
  const theme = useTheme();

  const [deliveryType, setDeliveryType] = useState<DeliveryType>("DELIVER");
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod | null>(null);
  const [address, setAddress] = useState("");

  const handleContinue = () => {
    if (!paymentMethod) return;
    router.push({
      pathname: `/business/orders/${supplierId}/review` as any,
      params: {
        paymentMethod,
        deliveryType,
        deliveryAddressText: address.trim() || DEFAULT_ADDRESS_PLACEHOLDER,
      },
    });
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>Deliver or collect?</Text>
        <View style={styles.segmentRow}>
          {DELIVERY_OPTIONS.map((option) => {
            const isSelected = option.value === deliveryType;
            return (
              <Pressable
                key={option.value}
                onPress={() => setDeliveryType(option.value)}
                style={[
                  styles.segment,
                  { borderColor: theme.colors.outline },
                  isSelected && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
                ]}
                accessibilityRole="button"
                accessibilityState={{ selected: isSelected }}
              >
                <Text style={[styles.segmentLabel, { color: isSelected ? theme.colors.onPrimary : theme.colors.onSurface }]}>
                  {option.label}
                </Text>
              </Pressable>
            );
          })}
        </View>

        <Text style={[styles.sectionTitle, styles.sectionSpacing, { color: theme.colors.onSurface }]}>
          {deliveryType === "COLLECT" ? "Collection address" : "Delivery address"}
        </Text>
        <TextInput
          value={address}
          onChangeText={setAddress}
          placeholder={DEFAULT_ADDRESS_PLACEHOLDER}
          placeholderTextColor={theme.colors.onSurfaceVariant}
          multiline
          style={[
            styles.addressInput,
            { borderColor: theme.colors.outline, color: theme.colors.onSurface, backgroundColor: theme.colors.surface },
          ]}
        />
        <Text style={[styles.addressHint, { color: theme.colors.onSurfaceVariant }]}>
          A real address book is coming soon -- this is used as-entered for now.
        </Text>

        <Text style={[styles.sectionTitle, styles.sectionSpacing, { color: theme.colors.onSurface }]}>How will you pay?</Text>
        {PAYMENT_OPTIONS.map((option) => {
          const isSelected = option.value === paymentMethod;
          return (
            <Pressable
              key={option.value}
              onPress={() => setPaymentMethod(option.value)}
              style={styles.row}
              accessibilityRole="radio"
              accessibilityState={{ checked: isSelected }}
            >
              <View style={styles.rowText}>
                <Text style={[styles.rowLabel, { color: theme.colors.onSurface }]}>{option.label}</Text>
                <Text style={[styles.rowDescription, { color: theme.colors.onSurfaceVariant }]}>{option.description}</Text>
              </View>
              {isSelected && <Check size={18} color={theme.colors.primary} strokeWidth={2.5} />}
            </Pressable>
          );
        })}

        <Pressable
          onPress={() => Alert.alert("Coming soon", "Paying online isn't available yet, but it's on the way.")}
          style={styles.row}
          accessibilityRole="button"
          accessibilityLabel="Pay Online"
        >
          <View style={styles.rowIconLabel}>
            <CreditCard size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
            <View style={styles.rowText}>
              <Text style={[styles.rowLabel, { color: theme.colors.onSurface }]}>Pay Online (Card / Instant EFT)</Text>
              <Text style={[styles.rowDescription, { color: theme.colors.onSurfaceVariant }]}>Coming soon</Text>
            </View>
          </View>
        </Pressable>

        <Pressable
          onPress={handleContinue}
          disabled={!paymentMethod}
          style={[styles.continueButton, { backgroundColor: theme.colors.primary }, !paymentMethod && styles.continueButtonDisabled]}
          accessibilityRole="button"
          accessibilityLabel="Continue to review"
        >
          <Text style={[styles.continueLabel, { color: theme.colors.onPrimary }]}>Continue to Review</Text>
        </Pressable>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xl },
  sectionTitle: { ...typography.h2, fontWeight: "700", marginBottom: spacing.sm },
  sectionSpacing: { marginTop: spacing.lg },
  segmentRow: { flexDirection: "row", gap: spacing.sm },
  segment: { flex: 1, minHeight: 44, borderWidth: 1, borderRadius: radius.md, alignItems: "center", justifyContent: "center" },
  segmentLabel: { ...typography.body, fontWeight: "700" },
  addressInput: { borderWidth: 1, borderRadius: radius.md, padding: spacing.sm, minHeight: 72, textAlignVertical: "top", ...typography.body },
  addressHint: { ...typography.caption, marginTop: spacing.xs },
  row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", minHeight: 56, paddingVertical: spacing.sm },
  rowIconLabel: { flexDirection: "row", alignItems: "center", gap: spacing.sm, flex: 1 },
  rowText: { flex: 1, paddingRight: spacing.sm },
  rowLabel: { ...typography.body, fontWeight: "700" },
  rowDescription: { ...typography.bodySmall },
  continueButton: { marginTop: spacing.lg, minHeight: 48, borderRadius: radius.md, alignItems: "center", justifyContent: "center" },
  continueButtonDisabled: { opacity: 0.5 },
  continueLabel: { fontWeight: "700", fontSize: 15 },
});
