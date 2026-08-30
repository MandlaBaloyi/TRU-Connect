import React, { useState } from "react";
import { ActivityIndicator, Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Check } from "lucide-react-native";

import { DISCONNECT_REASONS } from "../../find-supplier/types";
import type { DisconnectReason } from "../../find-supplier/types";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  visible: boolean;
  supplierName: string;
  isSubmitting: boolean;
  onSubmit: (reason: DisconnectReason, details: string | null) => void;
  onClose: () => void;
}

/** Mirrors ReportSupplierSheet.tsx's own shape exactly, deliberately
 *  -- same reason-picker pattern, same "details always available, not
 *  just for Other" choice. This sheet's own submit button IS the real
 *  confirmation moment (destructive-coloured, requires a reason
 *  first) -- deliberately not preceded by a separate Alert.alert
 *  "are you sure" step too, since stacking two confirmations in a row
 *  for the same action reads as redundant rather than careful. */
export function DisconnectSupplierSheet({ visible, supplierName, isSubmitting, onSubmit, onClose }: Props) {
  const theme = useTheme();
  const [reason, setReason] = useState<DisconnectReason | null>(null);
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
            <Text style={[styles.title, { color: theme.colors.onSurface }]}>Why are you disconnecting?</Text>
            <Text style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}>
              {supplierName} will move to your disconnected suppliers list.
            </Text>

            {DISCONNECT_REASONS.map((option) => {
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
              placeholder="Anything else you'd like to add"
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
              accessibilityLabel="Confirm disconnect"
            >
              {isSubmitting ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.submitLabel}>Disconnect</Text>
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
