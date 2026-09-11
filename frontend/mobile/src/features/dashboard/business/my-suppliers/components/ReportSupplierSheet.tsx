import React, { useState } from "react";
import { ActivityIndicator, Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Check } from "lucide-react-native";

import { REPORT_REASONS } from "../../find-supplier/types";
import type { ReportReason } from "../../find-supplier/types";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  visible: boolean;
  supplierName: string;
  isSubmitting: boolean;
  onSubmit: (reason: ReportReason, details: string | null) => void;
  onClose: () => void;
}

/** Same bottom-sheet shape as CatalogSortSheet/CatalogCategoryFilterSheet
 *  -- one consistent presentation language across this whole screen's
 *  overlays. Reason is required (radio-style, same checkmark
 *  convention); details is always available, not just when "Other" is
 *  picked -- a business reporting SUSPECTED_SCAM might reasonably want
 *  to add real specifics without that meaning the preset reason itself
 *  was ambiguous (matches the backend's own SupplierReport.details
 *  docstring). */
export function ReportSupplierSheet({ visible, supplierName, isSubmitting, onSubmit, onClose }: Props) {
  const theme = useTheme();
  const [reason, setReason] = useState<ReportReason | null>(null);
  const [details, setDetails] = useState("");

  const handleClose = () => {
    setReason(null);
    setDetails("");
    onClose();
  };

  const handleSubmit = () => {
    if (!reason) return;
    onSubmit(reason, details.trim() || null);
  };

  return (
    <Modal visible={visible} animationType="fade" transparent onRequestClose={handleClose}>
      <Pressable style={styles.backdrop} onPress={handleClose}>
        <Pressable style={[styles.sheet, { backgroundColor: theme.colors.background }]} onPress={() => {}}>
          <ScrollView showsVerticalScrollIndicator={false}>
            <Text style={[styles.title, { color: theme.colors.onSurface }]}>Report {supplierName}</Text>
            <Text style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}>
              This creates a real record TruConnect can review. Only report a genuine concern.
            </Text>

            {REPORT_REASONS.map((option) => {
              const isSelected = option.value === reason;
              return (
                <Pressable
                  key={option.value}
                  onPress={() => setReason(option.value)}
                  style={styles.row}
                  accessibilityRole="radio"
                  accessibilityState={{ checked: isSelected }}
                >
                  <Text style={[styles.rowLabel, { color: theme.colors.onSurface }]}>{option.label}</Text>
                  {isSelected && <Check size={18} color={theme.colors.primary} strokeWidth={2.5} />}
                </Pressable>
              );
            })}

            <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Details (optional)</Text>
            <TextInput
              value={details}
              onChangeText={setDetails}
              placeholder="Anything else that would help us understand what happened"
              placeholderTextColor={theme.colors.onSurfaceVariant}
              multiline
              numberOfLines={4}
              style={[
                styles.input,
                { borderColor: theme.colors.outline, color: theme.colors.onSurface },
              ]}
            />

            <Pressable
              onPress={handleSubmit}
              disabled={!reason || isSubmitting}
              style={[
                styles.submit,
                { backgroundColor: theme.colors.error },
                (!reason || isSubmitting) && styles.submitDisabled,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Submit report"
            >
              {isSubmitting ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.submitLabel}>Submit report</Text>
              )}
            </Pressable>
          </ScrollView>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.4)", justifyContent: "flex-end" },
  sheet: { borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg, padding: spacing.lg, maxHeight: "85%" },
  title: { ...typography.h2, fontWeight: "700", marginBottom: 4 },
  subtitle: { ...typography.bodySmall, marginBottom: spacing.md },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    minHeight: 48,
    paddingVertical: spacing.sm,
  },
  rowLabel: { ...typography.body, flex: 1, paddingRight: spacing.sm },
  label: { ...typography.bodySmall, marginTop: spacing.md, marginBottom: 4 },
  input: {
    borderWidth: 1,
    borderRadius: radius.md,
    padding: spacing.sm,
    minHeight: 90,
    textAlignVertical: "top",
    ...typography.body,
  },
  submit: {
    marginTop: spacing.lg,
    minHeight: 48,
    borderRadius: radius.md,
    alignItems: "center",
    justifyContent: "center",
  },
  submitDisabled: { opacity: 0.5 },
  submitLabel: { color: "#FFFFFF", fontWeight: "700", fontSize: 15 },
});
