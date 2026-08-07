/**
 * OutstandingAmountCard — the "Money Owed To You" headline.
 *
 * AMOUNT MASKING: tapping the eye icon hides the headline number behind
 * a FIXED-length mask ("R • • • • •") regardless of the real amount's
 * digit count — deliberately not a dot-per-digit mask, since a bystander
 * could still estimate rough magnitude just by counting dots, which
 * defeats the point of hiding it. Scoped to ONLY this one headline
 * number: the customer count line, every per-customer amount in the
 * list below, and Analytics are all unaffected — this solves "someone
 * glancing at my phone can read the one big number", not a general
 * privacy-mode feature.
 *
 * SESSION-ONLY, matching every other piece of state in this feature
 * (see README: no persistence yet) — reopening the app always starts
 * visible again, even if it was hidden moments before closing.
 *
 * COLOUR: light surface card (theme.colors.surface), matching the
 * Order Book summary card style — recoloured on request, structure and
 * every behaviour below (masking, actions, grammar) is unchanged.
 */

import React, { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Eye, EyeOff } from "lucide-react-native";

import type { LoanBookSummary } from "../types";
import { formatCents } from "../services/loanMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/** Fixed-length regardless of the real amount — see docstring above for
 *  why a dot-per-digit mask would still leak magnitude. */
const MASKED_AMOUNT = "R • • • • •";

interface Props {
  summary: LoanBookSummary;
  onRecordSale?: () => void;
  onViewLoanBook?: () => void;
}

export function OutstandingAmountCard({ summary, onRecordSale, onViewLoanBook }: Props) {
  const theme = useTheme();
  const [isHidden, setIsHidden] = useState(false);

  // Grammar matters here: "1 customer owes you" vs "6 customers owe
  // you" — a plural verb reading as singular ("1 customer owe you")
  // would be the kind of small wrongness that undermines trust in
  // everything else the app says, even though it's just one word.
  const customerLabel =
    summary.customersOwingCount === 1
      ? "1 customer owes you"
      : `${summary.customersOwingCount} customers owe you`;

  return (
    <View style={[styles.card, { backgroundColor: theme.colors.surface }]}>
      <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>
        Money owed to you
      </Text>
      <View style={styles.amountRow}>
        <Text
          style={[styles.amount, { color: theme.colors.onSurface }]}
          accessibilityRole="text"
          accessibilityLabel={isHidden ? "Amount hidden" : formatCents(summary.totalOutstanding)}
        >
          {isHidden ? MASKED_AMOUNT : formatCents(summary.totalOutstanding)}
        </Text>
        <Pressable
          onPress={() => setIsHidden((prev) => !prev)}
          hitSlop={10}
          style={styles.eyeButton}
          accessibilityRole="button"
          accessibilityLabel={isHidden ? "Show amount" : "Hide amount"}
        >
          {isHidden ? (
            <EyeOff size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
          ) : (
            <Eye size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
          )}
        </Pressable>
      </View>
      <Text style={[styles.meta, { color: theme.colors.onSurfaceVariant }]}>
        {customerLabel}
      </Text>

      <View style={styles.actions}>
        {onRecordSale && (
          <Pressable
            onPress={onRecordSale}
            style={({ pressed }) => [
              styles.primaryAction,
              { backgroundColor: theme.colors.secondary },
              pressed && styles.pressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel="Record a credit sale"
          >
            <Text style={[styles.primaryActionText, { color: theme.colors.onSecondary }]}>
              Record sale
            </Text>
          </Pressable>
        )}
        {onViewLoanBook && (
          <Pressable
            onPress={onViewLoanBook}
            style={({ pressed }) => [
              styles.secondaryAction,
              { borderColor: theme.colors.outline },
              pressed && styles.pressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel="Open the loan book"
          >
            <Text style={[styles.secondaryActionText, { color: theme.colors.primary }]}>
              View loan book
            </Text>
          </Pressable>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: radius.lg, padding: spacing.lg, gap: spacing.xs },
  label: { ...typography.bodySmall },
  amountRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  amount: { ...typography.display },
  eyeButton: { padding: spacing.xs },
  meta: { ...typography.bodySmall },
  actions: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.md },
  primaryAction: {
    flex: 1,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
  },
  primaryActionText: { ...typography.body, fontWeight: "600" },
  secondaryAction: {
    flex: 1,
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radius.md,
    borderWidth: 1,
    paddingHorizontal: spacing.md,
  },
  secondaryActionText: { ...typography.body },
  pressed: { opacity: 0.75 },
});
