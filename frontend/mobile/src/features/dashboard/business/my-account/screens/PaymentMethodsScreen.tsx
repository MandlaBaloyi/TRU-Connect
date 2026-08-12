import React from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { CreditCard, Landmark, Plus, Star, Trash2, Wallet } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { Card, CardSection, ListCard, Note, StatusPill } from "@/components/lists/CardListUI";
import { spacing } from "@/theme/spacing";

import { usePaymentMethods } from "../hooks/usePaymentMethods";
import type { PaymentMethod } from "../types";

const METHOD_ICON = { CASH: Wallet, EFT: Landmark } as const;

/**
 * Cash and EFT are the two real, configurable payment methods (see
 * types.ts's note above PaymentMethodType for the full reasoning).
 * Card/gateway payments are a real future capability, shown honestly
 * as a navigable "Coming soon" row rather than a disabled control that
 * silently does nothing.
 *
 * These are the methods a future Stock Order flow will let a business
 * choose between per order — this screen only manages which ones
 * exist, not any specific order's choice.
 */
export default function PaymentMethodsScreen() {
  const router = useRouter();
  const theme = useTheme();
  const { paymentMethods, isLoading, removePaymentMethod, setDefaultPaymentMethod } = usePaymentMethods();

  const confirmRemove = (method: PaymentMethod) => {
    Alert.alert("Remove payment method", `Remove ${method.displayLabel}?`, [
      { text: "Cancel", style: "cancel" },
      { text: "Remove", style: "destructive", onPress: () => removePaymentMethod(method.id).catch(() => {}) },
    ]);
  };

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <CardSection title="Your payment methods">
          {paymentMethods.map((method) => {
            const Icon = METHOD_ICON[method.type];
            return (
              <ListCard
                key={method.id}
                icon={(c) => <Icon size={20} color={c} />}
                title={method.displayLabel}
                subtitle={method.maskedReference}
                badge={
                  method.isDefault ? (
                    <StatusPill label="Default" tone="on" />
                  ) : method.status === "PENDING_VERIFICATION" ? (
                    <StatusPill label="Pending" tone="warning" />
                  ) : undefined
                }
                action={
                  <View style={styles.actions}>
                    {!method.isDefault && (
                      <Pressable
                        onPress={() => setDefaultPaymentMethod(method.id).catch(() => {})}
                        accessibilityRole="button"
                        accessibilityLabel={`Make ${method.displayLabel} default`}
                        hitSlop={8}
                      >
                        <Star size={18} color={theme.colors.onSurfaceVariant} />
                      </Pressable>
                    )}
                    {method.type !== "CASH" && (
                      <Pressable
                        onPress={() => confirmRemove(method)}
                        accessibilityRole="button"
                        accessibilityLabel={`Remove ${method.displayLabel}`}
                        hitSlop={8}
                      >
                        <Trash2 size={18} color={theme.colors.error} />
                      </Pressable>
                    )}
                  </View>
                }
              />
            );
          })}
          <Card
            icon={(c) => <CreditCard size={20} color={c} />}
            label="Card & gateway payments"
            status={<StatusPill label="Coming soon" tone="off" />}
            onPress={() => router.push("/business/my-account/card-payments" as any)}
          />
        </CardSection>

        <CardSection>
          <Card
            icon={(c) => <Plus size={20} color={c} />}
            label="Add EFT bank account"
            onPress={() => router.push("/business/my-account/add-payment-method" as any)}
          />
        </CardSection>

        <Note>
          Cash is recorded when a payment is confirmed. EFT is recorded and backed by your bank's own digital
          trail. TruConnect never stores full account numbers, card numbers, PINs, or CVVs.
        </Note>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.xl },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  actions: { flexDirection: "row", gap: spacing.md, alignItems: "center" },
});
