/**
 * LoanDetailsScreen — one entry, its payment history, and the actions.
 * Theme-aware. Now includes Call/WhatsApp contact actions and a
 * shareable receipt (see ContactActionsRow, LoanReceiptCard,
 * useShareReceipt).
 */

import React, { useState } from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { MD3Theme, useTheme } from "react-native-paper";
import { Eye, Share2 } from "lucide-react-native";

import { useCustomer, useLoan, useLoanPayments } from "../hooks";
import { useShareReceipt } from "../hooks/useShareReceipt";
import { formatCents } from "../services/loanMapper";
import { buildReceiptData, type ReceiptData } from "../services/receiptService";
import { recordReceiptEvent } from "../api/loanBookApi";
import { formatAge } from "../algorithms/agingCalculator";
import { describeOverdueFact } from "../algorithms/riskIndicator";
import {
  ContactActionsRow,
  CustomerAvatar,
  LoanReceiptCard,
  LoanStatusBadge,
  PaymentCard,
  ReasonPromptModal,
  ReceiptPreviewModal,
} from "../components";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";

// VERIFY: source the real logged-in business owner's first name once
// useAuth() (or equivalent) is confirmed — see
// services/receiptService.ts's buildFromLabel() docstring for why this
// is passed in rather than looked up inside the receipt logic itself.
// Falls back to "Sent via TruConnect" (buildFromLabel's own default)
// until this is wired to the real session.
const OWNER_FIRST_NAME: string | undefined = undefined;

export default function LoanDetailsScreen() {
  const router = useRouter();
  const theme = useTheme();
  const { loanId } = useLocalSearchParams<{ loanId: string }>();
  const { loan, isLoading, isError, notFound, refetch } = useLoan(loanId ?? "");
  const { customer } = useCustomer(loan?.entry.customerId ?? "");
  const { deleteEntry, isDeletingEntry } = useLoanPayments();
  const { shareReceipt, pendingReceipt, receiptRef, isSharing, error: shareError } = useShareReceipt();
  const [previewData, setPreviewData] = useState<ReceiptData | null>(null);
  const [deleteModalVisible, setDeleteModalVisible] = useState(false);

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (notFound || isError || !loan) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState
          message={
            notFound
              ? "This purchase no longer exists."
              : "Could not load this purchase. Check your connection and try again."
          }
          onRetry={notFound ? undefined : refetch}
        />
      </ScreenContainer>
    );
  }

  const customerName = customer?.customer.name ?? "Customer";
  const overdueFact = describeOverdueFact(loan.entry, loan.payments);

  const handleConfirmDelete = async (reason?: string) => {
    setDeleteModalVisible(false);
    await deleteEntry({ entryId: loan.entry.id, reason });
    router.back();
  };

  const handleShareReceipt = () => {
    if (!customer) return;
    recordReceiptEvent(loan.entry.id, loan.entry.customerId, "RECEIPT_SHARED").catch(() => {});
    shareReceipt(loan, customer.customer, OWNER_FIRST_NAME);
  };

  const handleViewReceipt = () => {
    if (!customer) return;
    recordReceiptEvent(loan.entry.id, loan.entry.customerId, "RECEIPT_VIEWED").catch(() => {});
    setPreviewData(buildReceiptData(loan, customer.customer, OWNER_FIRST_NAME));
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        {/* RAW, not tappable — this screen already IS the customer's
            purchase detail; there's nowhere further for a tap here to
            usefully go. An earlier version wrapped this in a Pressable
            that pushed a second, duplicate Customer screen on top of
            the real one (fixed separately), which is exactly the kind
            of thing an implied-but-empty tap target invites. Matches
            Customer screen's own header exactly: avatar, name, phone,
            nothing else. */}
        <View style={styles.customerRow}>
          <CustomerAvatar name={customerName} seed={loan.entry.customerId} size={52} />
          <View style={styles.customerText}>
            <Text style={[styles.customerName, { color: theme.colors.onSurface }]}>{customerName}</Text>
            {customer?.customer.phone && (
              <Text style={[styles.customerPhone, { color: theme.colors.onSurfaceVariant }]}>
                {customer.customer.phone}
              </Text>
            )}
          </View>
        </View>

        <ContactActionsRow
          phone={customer?.customer.phone}
          customerName={customerName}
          outstandingAmountLabel={formatCents(loan.outstandingAmount)}
        />

        <View style={styles.amountBlock}>
          <Text style={[styles.amountLabel, { color: theme.colors.onSurfaceVariant }]}>Still owed</Text>
          <Text style={[styles.amount, { color: theme.colors.onBackground }]}>
            {formatCents(loan.outstandingAmount)}
          </Text>
          {loan.amountPaid > 0 && (
            <Text style={[styles.amountMeta, { color: theme.colors.onSurfaceVariant }]}>
              {formatCents(loan.amountPaid)} paid of {formatCents(loan.entry.originalAmount)}
            </Text>
          )}
          <LoanStatusBadge status={loan.status} detail={overdueFact ?? undefined} />
        </View>

        <View style={styles.detailBlock}>
          <DetailRow label="Sale date" value={formatAge(loan.ageInDays)} theme={theme} />
          {loan.entry.description && <DetailRow label="For" value={loan.entry.description} theme={theme} />}
          <DetailRow label="Original amount" value={formatCents(loan.entry.originalAmount)} theme={theme} />
        </View>

        {loan.outstandingAmount > 0 && (
          <Pressable
            style={({ pressed }) => [
              styles.primaryButton,
              { backgroundColor: theme.colors.secondary },
              pressed && styles.pressed,
            ]}
            onPress={() => router.push(`/business/loan-book/add-payment?loanId=${loan.entry.id}`)}
            accessibilityRole="button"
            accessibilityLabel="Record a payment"
          >
            <Text style={[styles.primaryButtonText, { color: theme.colors.onSecondary }]}>
              Record payment
            </Text>
          </Pressable>
        )}

        <View style={styles.receiptActionsRow}>
          <Pressable
            style={({ pressed }) => [
              styles.receiptAction,
              { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
              pressed && styles.pressed,
            ]}
            onPress={handleViewReceipt}
            disabled={!customer}
            accessibilityRole="button"
            accessibilityLabel="View a receipt for this purchase"
          >
            <Eye size={18} color={theme.colors.onSurface} strokeWidth={2} />
            <Text style={[styles.receiptActionText, { color: theme.colors.onSurface }]}>
              View receipt
            </Text>
          </Pressable>

          <Pressable
            style={({ pressed }) => [
              styles.receiptAction,
              { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
              pressed && styles.pressed,
            ]}
            onPress={handleShareReceipt}
            disabled={!customer || isSharing}
            accessibilityRole="button"
            accessibilityLabel="Share a receipt for this purchase"
          >
            {isSharing ? (
              <ActivityIndicator color={theme.colors.onSurface} />
            ) : (
              <>
                <Share2 size={18} color={theme.colors.onSurface} strokeWidth={2} />
                <Text style={[styles.receiptActionText, { color: theme.colors.onSurface }]}>
                  Share receipt
                </Text>
              </>
            )}
          </Pressable>
        </View>
        {shareError && <Text style={[styles.error, { color: theme.colors.error }]}>{shareError}</Text>}

        <View style={styles.historyBlock}>
          <Text style={[styles.historyTitle, { color: theme.colors.onSurface }]}>
            {loan.payments.length === 0
              ? "No payments yet"
              : loan.payments.length === 1
                ? "1 payment"
                : `${loan.payments.length} payments`}
          </Text>
          {loan.payments.map((payment) => (
            <PaymentCard key={payment.id} payment={payment} />
          ))}
        </View>

        <Pressable
          onPress={() => setDeleteModalVisible(true)}
          disabled={isDeletingEntry}
          style={styles.deleteButton}
          accessibilityRole="button"
          accessibilityLabel="Remove this purchase"
        >
          <Text style={[styles.deleteText, { color: theme.colors.error }]}>Remove this purchase</Text>
        </Pressable>
      </ScrollView>

      {/* OFF-SCREEN CAPTURE TARGET — see useShareReceipt's docstring.
          Rendered far outside the viewport (not display:none, which some
          capture backends fail to rasterize) only while a share is in
          flight, then unmounted again. Never visible to the user. */}
      {pendingReceipt && (
        <View style={styles.offscreen} pointerEvents="none">
          <LoanReceiptCard ref={receiptRef} data={pendingReceipt} />
        </View>
      )}

      {/* ON-SCREEN preview — "View receipt". Reuses the exact same
          component and data shape as the off-screen capture target
          above, just rendered visibly instead of captured. */}
      <ReceiptPreviewModal
        visible={previewData !== null}
        data={previewData}
        onClose={() => setPreviewData(null)}
      />

      <ReasonPromptModal
        visible={deleteModalVisible}
        title="Remove this purchase?"
        description={`This moves the ${formatCents(loan.entry.originalAmount)} recorded for ${customerName} to Trash. It can be restored for 7 days.`}
        confirmLabel="Remove"
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteModalVisible(false)}
      />
    </ScreenContainer>
  );
}

function DetailRow({ label, value, theme }: { label: string; value: string; theme: MD3Theme }) {
  return (
    <View style={styles.detailRow}>
      <Text style={[styles.detailLabel, { color: theme.colors.onSurfaceVariant }]}>{label}</Text>
      <Text style={[styles.detailValue, { color: theme.colors.onSurface }]}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  content: { padding: spacing.md, paddingBottom: spacing.xxl, gap: spacing.lg },
  centre: { paddingVertical: spacing.xxl, alignItems: "center" },
  customerRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
  },
  customerText: { flex: 1 },
  customerName: { ...typography.h2 },
  customerPhone: { ...typography.bodySmall },
  amountBlock: { gap: spacing.xs, alignItems: "flex-start" },
  amountLabel: { ...typography.bodySmall },
  amount: { ...typography.display },
  amountMeta: { ...typography.bodySmall },
  detailBlock: { gap: spacing.sm },
  detailRow: { flexDirection: "row", justifyContent: "space-between", gap: spacing.md },
  detailLabel: { ...typography.body },
  detailValue: { ...typography.body, fontWeight: "600" },
  primaryButton: { minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radius.md },
  primaryButtonText: { ...typography.h2 },
  pressed: { opacity: 0.8 },
  receiptActionsRow: { flexDirection: "row", gap: spacing.sm },
  receiptAction: {
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
  receiptActionText: { ...typography.body, fontWeight: "600" },
  error: { ...typography.bodySmall },
  historyBlock: { gap: spacing.xs },
  historyTitle: { ...typography.h2, marginBottom: spacing.xs },
  deleteButton: { minHeight: 44, justifyContent: "center", alignItems: "center" },
  deleteText: { ...typography.body },
  offscreen: { position: "absolute", top: -10000, left: -10000 },
});
