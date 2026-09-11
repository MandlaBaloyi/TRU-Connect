import React, { useEffect, useState } from "react";
import { ActivityIndicator, Modal, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useTheme } from "react-native-paper";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  visible: boolean;
  currentValue: number;
  unit: string;
  isSubmitting: boolean;
  onSave: (value: number) => void;
  onClose: () => void;
  /** Overridable so this same component serves both the per-product
   *  threshold (InventoryDetailScreen) and the global default
   *  threshold (the "⋮" menu's own settings modal) rather than two
   *  near-identical components. */
  title?: string;
  hint?: string;
}

export function ThresholdModal({
  visible,
  currentValue,
  unit,
  isSubmitting,
  onSave,
  onClose,
  title = "Low stock threshold",
  hint = "TruConnect will mark this product \"Low stock\" once on-hand quantity drops to this number or below.",
}: Props) {
  const theme = useTheme();
  const [text, setText] = useState(String(currentValue));

  useEffect(() => {
    if (visible) setText(String(currentValue));
  }, [visible, currentValue]);

  const parsed = Number.parseInt(text, 10);
  const isValid = Number.isFinite(parsed) && parsed >= 0;

  return (
    <Modal visible={visible} animationType="fade" transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={[styles.sheet, { backgroundColor: theme.colors.background }]}>
          <Text style={[styles.title, { color: theme.colors.onSurface }]}>{title}</Text>
          <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>{hint}</Text>
          <TextInput
            value={text}
            onChangeText={setText}
            keyboardType="number-pad"
            style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            accessibilityLabel="Low stock threshold"
          />
          <Text style={[styles.unitLabel, { color: theme.colors.onSurfaceVariant }]}>{unit.toLowerCase()}</Text>

          <View style={styles.buttonRow}>
            <Pressable onPress={onClose} style={styles.secondaryButton} accessibilityRole="button" accessibilityLabel="Cancel">
              <Text style={[styles.secondaryButtonText, { color: theme.colors.onSurfaceVariant }]}>Cancel</Text>
            </Pressable>
            <Pressable
              onPress={() => isValid && onSave(parsed)}
              disabled={!isValid || isSubmitting}
              style={[
                styles.primaryButton,
                { backgroundColor: isValid ? theme.colors.primary : theme.colors.surfaceDisabled },
              ]}
              accessibilityRole="button"
              accessibilityLabel="Save"
            >
              {isSubmitting ? (
                <ActivityIndicator color={theme.colors.onPrimary} />
              ) : (
                <Text
                  style={[
                    styles.primaryButtonText,
                    { color: isValid ? theme.colors.onPrimary : theme.colors.onSurfaceDisabled },
                  ]}
                >
                  Save
                </Text>
              )}
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.4)", justifyContent: "flex-end" },
  sheet: { borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg, padding: spacing.lg, gap: spacing.sm },
  title: { ...typography.h2, fontWeight: "700" },
  hint: { ...typography.bodySmall },
  input: {
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    minHeight: 48,
    ...typography.body,
    marginTop: spacing.xs,
  },
  unitLabel: { ...typography.caption },
  buttonRow: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.sm },
  secondaryButton: { flex: 1, minHeight: 48, alignItems: "center", justifyContent: "center" },
  secondaryButtonText: { ...typography.body, fontWeight: "600" },
  primaryButton: { flex: 1, minHeight: 48, alignItems: "center", justifyContent: "center", borderRadius: radius.md },
  primaryButtonText: { ...typography.body, fontWeight: "700" },
});
