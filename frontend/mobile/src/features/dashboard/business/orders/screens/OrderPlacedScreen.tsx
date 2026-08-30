import React from "react";
import { Alert, Linking, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { CheckCircle2, MessageCircle } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { formatCents } from "../../../supplier/products/services/productMapper";
import { buildWhatsAppUrl } from "../../loan-book/services/contactActions";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { useSupplierProducts } from "../../find-supplier/hooks/useSupplierProducts";
import type { PaymentMethod } from "../types";

/**
 * Step 3 of 3 -- the real Stock Order ID, real instructions, and for
 * Proof of Payment specifically, a real way to actually send it.
 *
 * Fetches the supplier's own contact details independently, via the
 * same catalog query the Stock Catalogue screen itself already uses
 * -- the cart this order came from is already cleared by this point,
 * so nothing here can rely on it.
 *
 * "Send via TRU Connect" is shown, real, and marked Coming soon --
 * honest that in-app delivery isn't wired yet, without hiding that
 * it's coming.
 */
export default function OrderPlacedScreen() {
  const { supplierId, orderId, totalCents, instructions, paymentMethod, supplierName } = useLocalSearchParams<{
    supplierId: string;
    orderId: string;
    totalCents: string;
    instructions: string;
    paymentMethod: PaymentMethod;
    supplierName: string;
  }>();
  const router = useRouter();
  const theme = useTheme();
  const { contact } = useSupplierProducts(supplierId ?? "", { limit: 1 });

  const handleSendViaWhatsApp = () => {
    if (!contact?.whatsappNumber) {
      Alert.alert("No WhatsApp number", "This supplier hasn't added a WhatsApp number yet.");
      return;
    }
    const message = `Hi, I've placed order ${orderId} for ${formatCents(Number(totalCents))} on TRU Connect. Here's my proof of payment.`;
    Linking.openURL(buildWhatsAppUrl(contact.whatsappNumber, message)).catch(() => {
      // Silently ignored -- same reasoning as every other WhatsApp
      // link in this app: wa.me degrades to a normal web page when
      // the app isn't installed, so a failure here means no route at
      // all, nothing more useful to do.
    });
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <CheckCircle2 size={48} color={theme.colors.primary} strokeWidth={1.5} />
          <Text style={[styles.title, { color: theme.colors.onSurface }]}>Order placed</Text>
          <Text style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}>
            {supplierName ? `Sent to ${supplierName}` : "Your order has been sent to the supplier"}
          </Text>
        </View>

        <View style={[styles.card, { borderColor: theme.colors.outlineVariant }]}>
          <View style={styles.cardRow}>
            <Text style={[styles.cardLabel, { color: theme.colors.onSurfaceVariant }]}>Order ID</Text>
            <Text style={[styles.cardValue, { color: theme.colors.onSurface }]} selectable>
              {orderId}
            </Text>
          </View>
          <View style={styles.cardRow}>
            <Text style={[styles.cardLabel, { color: theme.colors.onSurfaceVariant }]}>Total</Text>
            <Text style={[styles.cardValue, { color: theme.colors.onSurface }]}>{formatCents(Number(totalCents))}</Text>
          </View>
        </View>

        {instructions ? (
          <Text style={[styles.instructions, { color: theme.colors.onSurface }]}>{instructions}</Text>
        ) : null}

        {paymentMethod === "PROOF_OF_PAYMENT" && (
          <View style={styles.proofSection}>
            <Text style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>Send your proof of payment</Text>
            <Pressable
              onPress={handleSendViaWhatsApp}
              style={[styles.proofButton, { backgroundColor: theme.colors.surfaceVariant }]}
              accessibilityRole="button"
              accessibilityLabel="Send via WhatsApp"
            >
              <MessageCircle size={20} color={theme.colors.onSurface} strokeWidth={2} />
              <Text style={[styles.proofButtonLabel, { color: theme.colors.onSurface }]}>Send via WhatsApp</Text>
            </Pressable>
            <Pressable
              onPress={() => Alert.alert("Coming soon", "Sending proof of payment directly in TRU Connect isn't available yet, but it's on the way.")}
              style={[styles.proofButton, { backgroundColor: theme.colors.surfaceVariant }]}
              accessibilityRole="button"
              accessibilityLabel="Send via TRU Connect"
            >
              <Text style={[styles.proofButtonLabel, { color: theme.colors.onSurface }]}>Send via TRU Connect</Text>
              <Text style={[styles.comingSoonTag, { color: theme.colors.onSurfaceVariant }]}>Coming soon</Text>
            </Pressable>
          </View>
        )}

        <Pressable
          onPress={() => router.push(`/business/find-supplier/${supplierId}` as any)}
          style={[styles.continueButton, { borderColor: theme.colors.outline }]}
          accessibilityRole="button"
          accessibilityLabel="Continue browsing"
        >
          <Text style={[styles.continueLabel, { color: theme.colors.onSurface }]}>Continue browsing</Text>
        </Pressable>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xl },
  header: { alignItems: "center", gap: spacing.xs, paddingVertical: spacing.lg },
  title: { ...typography.h1, fontWeight: "700" },
  subtitle: { ...typography.body, textAlign: "center" },
  card: { borderWidth: 1, borderRadius: radius.md, padding: spacing.md, gap: spacing.sm, marginTop: spacing.md },
  cardRow: { flexDirection: "row", justifyContent: "space-between" },
  cardLabel: { ...typography.bodySmall },
  cardValue: { ...typography.body, fontWeight: "700" },
  instructions: { ...typography.body, marginTop: spacing.md, lineHeight: 20 },
  proofSection: { marginTop: spacing.lg, gap: spacing.sm },
  sectionTitle: { ...typography.body, fontWeight: "700" },
  proofButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.sm,
    minHeight: 48,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
  },
  proofButtonLabel: { ...typography.body, fontWeight: "600" },
  comingSoonTag: { ...typography.caption },
  continueButton: { marginTop: spacing.xl, minHeight: 48, borderWidth: 1, borderRadius: radius.md, alignItems: "center", justifyContent: "center" },
  continueLabel: { fontWeight: "700", fontSize: 15 },
});
