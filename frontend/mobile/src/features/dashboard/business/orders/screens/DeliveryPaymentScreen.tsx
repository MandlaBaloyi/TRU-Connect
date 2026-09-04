import React, { useEffect, useState } from "react";
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Banknote, Check, CreditCard, MapPin, Receipt } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useSavedDeliveryAddress } from "../hooks/useSavedDeliveryAddress";
import type { DeliveryType, PaymentMethod } from "../types";

const DELIVERY_OPTIONS: { value: DeliveryType; label: string }[] = [
  { value: "DELIVER", label: "Deliver" },
  { value: "COLLECT", label: "Collect" },
];

const PAYMENT_OPTIONS: { value: PaymentMethod; label: string; description: string; Icon: typeof Banknote }[] = [
  { value: "CASH", label: "Cash", description: "Pay on delivery or collection", Icon: Banknote },
  {
    value: "PROOF_OF_PAYMENT",
    label: "Proof of Payment",
    description: "Pay the supplier directly, then send proof",
    Icon: Receipt,
  },
];

/**
 * Step 1 of 3 -- a real, full screen, not a bottom sheet.
 *
 * DELIVER vs COLLECT get genuinely different address handling, not
 * the same text box with a different label -- confirmed directly
 * after checking the actual backend: a real, saved business address
 * doesn't exist yet (useSavedDeliveryAddress is the ready-to-wire
 * plug-in point for when it does), so Deliver keeps a free-text field
 * for now. Collect is different in kind, not just missing data --
 * checking SupplierProfile directly confirmed there's no real
 * collection address field there at all, only a general suburb/city
 * "location" column explicitly documented as never meant to hold a
 * full street address. A business genuinely can't type the supplier's
 * own address, so Collect shows a real, honest placeholder instead of
 * an editable field that would silently accept the wrong thing.
 *
 * A REAL THIRD PAYMENT OPTION sits here -- "Pay Online (Card / Instant
 * EFT)". Tapping it shows "Coming soon" and never actually selects
 * it -- the real backend already correctly rejects PAYFAST as
 * unavailable, so this is never even attempted.
 *
 * NO "Confirm Order" BUTTON HERE -- deliberately. This screen only
 * collects the delivery/payment choice; the real submission lives on
 * the Review Order screen next.
 */
export default function DeliveryPaymentScreen() {
  const { supplierId } = useLocalSearchParams<{ supplierId: string }>();
  const router = useRouter();
  const theme = useTheme();
  const { savedAddress } = useSavedDeliveryAddress();

  const [deliveryType, setDeliveryType] = useState<DeliveryType>("DELIVER");
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod | null>(null);
  const [address, setAddress] = useState("");

  useEffect(() => {
    if (savedAddress) setAddress(savedAddress);
  }, [savedAddress]);

  const handleContinue = () => {
    if (!paymentMethod) return;
    if (deliveryType === "DELIVER" && !address.trim()) {
      Alert.alert("Address needed", "Enter a delivery address to continue.");
      return;
    }
    router.push({
      pathname: `/business/orders/${supplierId}/review` as any,
      params: {
        paymentMethod,
        deliveryType,
        deliveryAddressText:
          deliveryType === "DELIVER" ? address.trim() : "Provided by the supplier upon collection",
      },
    });
  };

  const handlePayOnline = () => {
    Alert.alert("Coming soon", "Paying online isn't available yet, but it's on the way.");
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
        {deliveryType === "DELIVER" ? (
          <TextInput
            value={address}
            onChangeText={setAddress}
            placeholder="Enter your delivery address"
            placeholderTextColor={theme.colors.onSurfaceVariant}
            multiline
            style={[
              styles.addressInput,
              { borderColor: theme.colors.outline, color: theme.colors.onSurface, backgroundColor: theme.colors.surface },
            ]}
          />
        ) : (
          <View style={[styles.collectNotice, { borderColor: theme.colors.outline, backgroundColor: theme.colors.surfaceVariant }]}>
            <MapPin size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
            <Text style={[styles.collectNoticeText, { color: theme.colors.onSurfaceVariant }]}>
              Your supplier's collection address will appear here once they've added one.
            </Text>
          </View>
        )}

        <Text style={[styles.sectionTitle, styles.sectionSpacing, { color: theme.colors.onSurface }]}>How will you pay?</Text>
        {PAYMENT_OPTIONS.map((option) => {
          const isSelected = option.value === paymentMethod;
          return (
            <Pressable
              key={option.value}
              onPress={() => setPaymentMethod(option.value)}
              style={[
                styles.optionRow,
                { borderColor: theme.colors.outline },
                isSelected && { borderColor: theme.colors.primary, backgroundColor: theme.colors.primaryContainer },
              ]}
              accessibilityRole="radio"
              accessibilityState={{ checked: isSelected }}
            >
              <option.Icon size={22} color={isSelected ? theme.colors.primary : theme.colors.onSurfaceVariant} strokeWidth={2} />
              <View style={styles.rowText}>
                <Text style={[styles.rowLabel, { color: theme.colors.onSurface }]}>{option.label}</Text>
                <Text style={[styles.rowDescription, { color: theme.colors.onSurfaceVariant }]}>{option.description}</Text>
              </View>
              {isSelected && <Check size={18} color={theme.colors.primary} strokeWidth={2.5} />}
            </Pressable>
          );
        })}

        <Pressable
          onPress={handlePayOnline}
          style={[styles.optionRow, { borderColor: theme.colors.outline }]}
          accessibilityRole="button"
          accessibilityLabel="Pay Online"
        >
          <CreditCard size={22} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
          <View style={styles.rowText}>
            <Text style={[styles.rowLabel, { color: theme.colors.onSurface }]}>Pay Online (Card / Instant EFT)</Text>
            <Text style={[styles.rowDescription, { color: theme.colors.onSurfaceVariant }]}>Coming soon</Text>
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
  collectNotice: { flexDirection: "row", alignItems: "flex-start", gap: spacing.sm, borderWidth: 1, borderRadius: radius.md, padding: spacing.sm },
  collectNoticeText: { ...typography.bodySmall, flex: 1 },
  optionRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    minHeight: 56,
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.sm,
    marginBottom: spacing.sm,
  },
  rowText: { flex: 1, paddingRight: spacing.sm },
  rowLabel: { ...typography.body, fontWeight: "700" },
  rowDescription: { ...typography.bodySmall },
  continueButton: { marginTop: spacing.lg, minHeight: 48, borderRadius: radius.md, alignItems: "center", justifyContent: "center" },
  continueButtonDisabled: { opacity: 0.5 },
  continueLabel: { fontWeight: "700", fontSize: 15 },
});
