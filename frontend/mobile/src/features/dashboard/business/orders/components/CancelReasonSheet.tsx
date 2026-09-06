import React, { useState } from "react";
import { ActivityIndicator, Modal, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Check, X } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { CANCEL_REASON_LABELS } from "../types";
import type { CancelReason } from "../types";

interface Props {
  visible: boolean;
  isSubmitting: boolean;
  onSubmit: (reason: CancelReason, details?: string) => void;
  onClose: () => void;
}

const REASONS: CancelReason[] = ["changed_mind", "found_alternative", "ordered_by_mistake", "other"];

/**
 * The business's own self-service cancel -- only ever reachable while
 * the order is still PENDING_SUPPLIER_APPROVAL (DeliveryPaymentScreen
 * -> ... -> OrderDetailSheet only shows the entry point for this in
 * that state at all). Same visual shape as the supplier's own
 * DeclineReasonSheet/CancelReasonSheet, deliberately reused rather
 * than reinvented.
 */
export function CancelReasonSheet({ visible, isSubmitting, onSubmit, onClose }: Props) {
  const theme = useTheme();
  const [reason, setReason] = useState<CancelReason | null>(null);
  const [details, setDetails] = useState("");

  const handleClose = () => {
    setReason(null);
    setDetails("");
    onClose();
  };

  const handleSubmit = () => {
    if (!reason) return;
    onSubmit(reason, details.trim() || undefined);
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={handleClose}>
      <Pressable style={styles.backdrop} onPress={handleClose}>
        <Pressable style={[styles.sheet, { backgroundColor: theme.colors.background }]} onPress={() => {}}>
          <View style={styles.header}>
            <Text style={[styles.title, { color: theme.colors.onSurface }]}>Cancel this order</Text>
            <Pressable onPress={handleClose} hitSlop={10} accessibilityRole="button" accessibilityLabel="Close">
              <X size={22} color={theme.colors.onSurfaceVariant} strokeWidth={2.2} />
            </Pressable>
          </View>
          <Text style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}>
            Your supplier hasn't approved this yet -- they'll be notified it's been cancelled.
          </Text>

          {REASONS.map((option) => {
            const isSelected = option === reason;
            return (
              <Pressable
                key={option}
                onPress={() => setReason(option)}
                style={[
                  styles.optionRow,
                  { borderColor: theme.colors.outline },
                  isSelected && { borderColor: theme.colors.error, backgroundColor: theme.colors.errorContainer },
                ]}
                accessibilityRole="radio"
                accessibilityState={{ checked: isSelected }}
              >
                <Text style={[styles.optionLabel, { color: theme.colors.onSurface }]}>
                  {CANCEL_REASON_LABELS[option]}
                </Text>
                {isSelected && <Check size={18} color={theme.colors.error} strokeWidth={2.5} />}
              </Pressable>
            );
          })}

          <Text style={[styles.detailsLabel, { color: theme.colors.onSurfaceVariant }]}>
            Add a note (optional)
          </Text>
          <TextInput
            value={details}
            onChangeText={setDetails}
            placeholder="e.g. Found it cheaper down the road"
            placeholderTextColor={theme.colors.onSurfaceVariant}
            multiline
            style={[
              styles.detailsInput,
              { borderColor: theme.colors.outline, color: theme.colors.onSurface, backgroundColor: theme.colors.surface },
            ]}
          />

          <Pressable
            onPress={handleSubmit}
            disabled={!reason || isSubmitting}
            style={[
              styles.submitButton,
              { backgroundColor: theme.colors.error },
              (!reason || isSubmitting) && styles.submitButtonDisabled,
            ]}
            accessibilityRole="button"
            accessibilityLabel="Confirm cancellation"
          >
            {isSubmitting ? (
              <ActivityIndicator color={theme.colors.onError} />
            ) : (
              <Text style={[styles.submitLabel, { color: theme.colors.onError }]}>Confirm Cancellation</Text>
            )}
          </Pressable>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.4)", justifyContent: "flex-end" },
  sheet: { borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg, padding: spacing.lg },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: spacing.xs },
  title: { ...typography.h2, fontWeight: "700" },
  subtitle: { ...typography.bodySmall, marginBottom: spacing.md },
  optionRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    minHeight: 52,
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.sm,
    marginBottom: spacing.sm,
  },
  optionLabel: { ...typography.body, fontWeight: "600" },
  detailsLabel: { ...typography.bodySmall, marginTop: spacing.sm, marginBottom: spacing.xs },
  detailsInput: { borderWidth: 1, borderRadius: radius.md, padding: spacing.sm, minHeight: 64, textAlignVertical: "top", ...typography.body },
  submitButton: { marginTop: spacing.lg, minHeight: 48, borderRadius: radius.md, alignItems: "center", justifyContent: "center" },
  submitButtonDisabled: { opacity: 0.5 },
  submitLabel: { fontWeight: "700", fontSize: 15 },
});
