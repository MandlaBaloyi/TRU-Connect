/**
 * ContactActionsRow — Call and WhatsApp buttons for a customer.
 *
 * Uses lucide icons (Phone, MessageCircle) rather than emoji, matching
 * LoanBookIcon/ProductCatalogueIcon's established icon language rather
 * than introducing a second visual system.
 *
 * Both actions hide entirely when there's no phone number, rather than
 * showing a disabled button — Customer.phone is optional (Doc 04 §3.4:
 * many informal customers are known by name and face only), so this is
 * a routine, expected case, not an error state.
 */

import React from "react";
import { Linking, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { MessageCircle, Phone } from "lucide-react-native";

import { buildDefaultLoanMessage, buildTelUrl, buildWhatsAppUrl } from "../services/contactActions";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  phone?: string;
  customerName: string;
  /** Included in the pre-filled WhatsApp message, e.g. "R 95.00". */
  outstandingAmountLabel?: string;
}

export function ContactActionsRow({ phone, customerName, outstandingAmountLabel }: Props) {
  const theme = useTheme();
  if (!phone) return null;

  const handleCall = () => {
    Linking.openURL(buildTelUrl(phone)).catch(() => {
      // Silently ignored: on a device with no telephony capability (e.g.
      // a Wi-Fi-only tablet), there is nothing more useful to do than
      // leave the app state unchanged. No dialler exists to hand off to.
    });
  };

  const handleWhatsApp = () => {
    const message = outstandingAmountLabel
      ? buildDefaultLoanMessage(customerName, outstandingAmountLabel)
      : undefined;
    Linking.openURL(buildWhatsAppUrl(phone, message)).catch(() => {
      // wa.me itself falls back to a web page when WhatsApp isn't
      // installed, so a failure here means something more fundamental
      // (no network route to open any URL at all) — nothing left to do.
    });
  };

  return (
    <View style={styles.row}>
      <Pressable
        onPress={handleCall}
        style={({ pressed }) => [
          styles.action,
          { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
          pressed && styles.pressed,
        ]}
        accessibilityRole="button"
        accessibilityLabel={`Call ${customerName}`}
      >
        <Phone size={18} color={theme.colors.onSurface} strokeWidth={2} />
        <Text style={[styles.label, { color: theme.colors.onSurface }]}>Call</Text>
      </Pressable>

      <Pressable
        onPress={handleWhatsApp}
        style={({ pressed }) => [
          styles.action,
          { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
          pressed && styles.pressed,
        ]}
        accessibilityRole="button"
        accessibilityLabel={`Message ${customerName} on WhatsApp`}
      >
        <MessageCircle size={18} color={theme.colors.onSurface} strokeWidth={2} />
        <Text style={[styles.label, { color: theme.colors.onSurface }]}>WhatsApp</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: spacing.sm },
  action: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.xs,
    minHeight: 48,
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
  },
  pressed: { opacity: 0.7 },
  label: { ...typography.body, fontWeight: "600" },
});
