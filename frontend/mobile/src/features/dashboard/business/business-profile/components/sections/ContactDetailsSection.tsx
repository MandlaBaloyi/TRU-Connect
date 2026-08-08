/** Contact Details — view-only summary. Edit lives on its own screen
 *  (my-business/contact-details.tsx). */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";

import type { ContactDetails } from "../../types";
import { EditButton } from "../EditButton";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  contact: ContactDetails;
}

function maskEmail(email: string): string {
  const [name, domain] = email.split("@");
  if (!domain || name.length <= 2) return email;
  return `${name.slice(0, 2)}${"*".repeat(Math.max(name.length - 2, 2))}@${domain}`;
}

export function ContactDetailsSection({ contact }: Props) {
  const theme = useTheme();
  const router = useRouter();

  const whatsappSummary = contact.whatsappNotUsed
    ? "Not used"
    : contact.whatsappSameAsPhone
      ? "Same as business phone"
      : contact.whatsapp;

  return (
    <View style={styles.viewMode}>
      {contact.phone && (
        <View style={styles.row}>
          <Text style={[styles.rowLabel, { color: theme.colors.onSurfaceVariant }]}>Phone</Text>
          <Text style={[styles.rowValue, { color: theme.colors.onSurface }]}>{contact.phone}</Text>
        </View>
      )}
      {contact.email && (
        <View style={styles.row}>
          <Text style={[styles.rowLabel, { color: theme.colors.onSurfaceVariant }]}>Email</Text>
          <Text style={[styles.rowValue, { color: theme.colors.onSurface }]}>{maskEmail(contact.email)}</Text>
        </View>
      )}
      <View style={styles.row}>
        <Text style={[styles.rowLabel, { color: theme.colors.onSurfaceVariant }]}>WhatsApp</Text>
        <Text style={[styles.rowValue, { color: theme.colors.onSurface }]}>{whatsappSummary}</Text>
      </View>
      <EditButton onPress={() => router.push("/business/my-business/contact-details")} />
    </View>
  );
}

const styles = StyleSheet.create({
  viewMode: { gap: spacing.sm },
  row: { flexDirection: "row", justifyContent: "space-between" },
  rowLabel: { ...typography.bodySmall },
  rowValue: { ...typography.body, fontWeight: "600" },
});
