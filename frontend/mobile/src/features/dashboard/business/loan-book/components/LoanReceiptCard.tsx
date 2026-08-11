/**
 * LoanReceiptCard — the visual receipt, captured as an image and shared.
 * See services/receiptService.ts for the data-assembly logic and the
 * full design rationale (why "Credit Sale Record" not "Invoice", why the
 * disclaimer line is load-bearing, why the reference code exists).
 *
 * RENDERED OFF-SCREEN FOR CAPTURE: this component is never meant to be
 * seen directly by the user in normal navigation — it's rendered
 * off-screen inside LoanDetailsScreen specifically so useShareReceipt
 * can capture it with react-native-view-shot. See that hook for how the
 * ref is wired up.
 *
 * FIXED WIDTH (not flex/responsive): a shared image needs a stable,
 * predictable size regardless of the device it was generated on —
 * unlike an on-screen component, this is never resized by the viewport,
 * so a fixed pixel width is correct here, not a shortcut.
 */

import React, { forwardRef } from "react";
import { StyleSheet, Text, View } from "react-native";
import { MD3Theme, useTheme } from "react-native-paper";

import type { ReceiptData } from "../services/receiptService";
import { RECEIPT_STATUS_LABEL } from "../services/receiptService";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

const RECEIPT_WIDTH = 360;

interface Props {
  data: ReceiptData;
}

export const LoanReceiptCard = forwardRef<View, Props>(function LoanReceiptCard({ data }, ref) {
  const theme = useTheme();
  const isPaid = data.status === "PAID";
  const isOverdue = data.status === "OVERDUE";

  const amountBlockColour = isPaid
    ? theme.colors.secondaryContainer
    : isOverdue
      ? theme.colors.errorContainer
      : theme.colors.surfaceVariant;
  const amountTextColour = isPaid
    ? theme.colors.onSecondaryContainer
    : isOverdue
      ? theme.colors.onErrorContainer
      : theme.colors.onSurfaceVariant;

  return (
    <View
      ref={ref}
      collapsable={false}
      style={[styles.card, { width: RECEIPT_WIDTH, backgroundColor: theme.colors.background }]}
    >
      <Text style={[styles.wordmark, { color: theme.colors.primary }]}>TruConnect</Text>

      <Text style={[styles.title, { color: theme.colors.onBackground }]}>Credit Sale Record</Text>
      <View style={[styles.divider, { backgroundColor: theme.colors.outline }]} />

      <ReceiptRow label="For" value={data.customerName} theme={theme} />
      <ReceiptRow label="From" value={data.fromLabel} theme={theme} />
      <ReceiptRow label="Date" value={data.saleDateLabel} theme={theme} />
      {data.description && <ReceiptRow label="For" value={data.description} theme={theme} />}

      <View style={[styles.amountBlock, { backgroundColor: amountBlockColour }]}>
        <Text style={[styles.amountLabel, { color: amountTextColour }]}>
          {isPaid ? "Amount settled" : "Amount owed"}
        </Text>
        <Text style={[styles.amount, { color: amountTextColour }]}>
          {isPaid ? data.originalAmountLabel : data.outstandingAmountLabel}
        </Text>
        <Text style={[styles.statusLabel, { color: amountTextColour }]}>
          • {RECEIPT_STATUS_LABEL[data.status]}
        </Text>
      </View>

      {data.isPartlyPaid && (
        <View style={styles.breakdownBlock}>
          <ReceiptRow label="Original amount" value={data.originalAmountLabel} theme={theme} compact />
          <ReceiptRow label="Paid so far" value={data.amountPaidLabel} theme={theme} compact />
          <ReceiptRow label="Still owed" value={data.outstandingAmountLabel} theme={theme} compact emphasise />
        </View>
      )}

      <View style={[styles.divider, { backgroundColor: theme.colors.outline }]} />

      <Text style={[styles.disclaimer, { color: theme.colors.onSurfaceVariant }]}>
        This is a personal record between the parties. TruConnect does not lend money or collect
        payments.
      </Text>

      <Text style={[styles.reference, { color: theme.colors.onSurfaceVariant }]}>
        Reference: {data.referenceCode}
      </Text>
      <Text style={[styles.generatedAt, { color: theme.colors.onSurfaceVariant }]}>
        Generated {data.generatedAtLabel}
      </Text>

      <Text style={[styles.poweredBy, { color: theme.colors.onSurfaceVariant }]}>
        Powered by TruePoint
      </Text>
    </View>
  );
});

function ReceiptRow({
  label,
  value,
  theme,
  compact = false,
  emphasise = false,
}: {
  label: string;
  value: string;
  theme: MD3Theme;
  compact?: boolean;
  emphasise?: boolean;
}) {
  return (
    <View style={compact ? styles.compactRow : styles.row}>
      <Text style={[styles.rowLabel, { color: theme.colors.onSurfaceVariant }]}>{label}</Text>
      <Text
        style={[
          styles.rowValue,
          { color: theme.colors.onSurface },
          emphasise && { fontWeight: "700" },
        ]}
      >
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { padding: spacing.lg, gap: spacing.sm },
  wordmark: { ...typography.h2, fontWeight: "700" },
  title: { ...typography.h1, marginTop: spacing.xs },
  divider: { height: 1, marginVertical: spacing.sm },
  row: { flexDirection: "row", justifyContent: "space-between", gap: spacing.md, paddingVertical: 2 },
  compactRow: { flexDirection: "row", justifyContent: "space-between", gap: spacing.md, paddingVertical: 1 },
  rowLabel: { ...typography.bodySmall },
  rowValue: { ...typography.bodySmall, fontWeight: "600", textAlign: "right", flexShrink: 1 },
  amountBlock: {
    borderRadius: radius.md,
    padding: spacing.md,
    alignItems: "center",
    gap: 2,
    marginVertical: spacing.sm,
  },
  amountLabel: { ...typography.bodySmall },
  amount: { ...typography.display },
  statusLabel: { ...typography.caption, fontWeight: "600" },
  breakdownBlock: { gap: 2, marginBottom: spacing.sm },
  disclaimer: { ...typography.caption, lineHeight: 16 },
  reference: { ...typography.caption, marginTop: spacing.xs },
  generatedAt: { ...typography.caption },
  poweredBy: { ...typography.caption, textAlign: "center", marginTop: spacing.md },
});
