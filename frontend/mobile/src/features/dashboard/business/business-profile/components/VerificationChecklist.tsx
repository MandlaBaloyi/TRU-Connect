import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Check, Circle } from "lucide-react-native";

import type { VerificationStatus } from "../types";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  verification: VerificationStatus;
}

/** Every row uses the same neutral phrasing whether checked or not —
 *  "Business information" vs "✓ Business information", never anything
 *  implying an incomplete section makes the business untrustworthy.
 *  Matches the spec's explicit "Not verified yet", never "Unverified
 *  business" rule. */
export function VerificationChecklist({ verification }: Props) {
  const theme = useTheme();

  const rows: { label: string; done: boolean }[] = [
    { label: "Phone number verified", done: verification.phoneVerified },
    { label: "Email verified", done: verification.emailVerified },
    { label: "Business information", done: verification.businessInfoComplete },
    { label: "Business location", done: verification.locationComplete },
    // Identity verification and Business documents were here. They were
    // the SUPPLIER model's concepts on a business: the curtain gates who
    // may SELL, and an informal business is not checked in order to
    // shop. Neither had a backing system, so both showed a permanently
    // unticked box implying a review that was never going to happen.
  ];

  return (
    <View style={styles.wrapper}>
      {rows.map((row) => (
        <View key={row.label} style={styles.row}>
          {row.done ? (
            <Check size={16} color={theme.colors.secondary} strokeWidth={3} />
          ) : (
            <Circle size={16} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
          )}
          <Text style={[styles.label, { color: row.done ? theme.colors.onSurface : theme.colors.onSurfaceVariant }]}>
            {row.label}
          </Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: spacing.sm },
  row: { flexDirection: "row", alignItems: "center", gap: spacing.sm, minHeight: 24 },
  label: { ...typography.body },
});
