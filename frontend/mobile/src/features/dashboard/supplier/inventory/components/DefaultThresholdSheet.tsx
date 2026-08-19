/**
 * DefaultThresholdSheet — same bottom-sheet structure and interaction
 * as products/components/SortOptionsSheet.tsx: backdrop dismisses,
 * tapping a preset row applies it AND closes the sheet immediately,
 * no separate "Save" step. Presets are the common case; "Custom" is
 * the one row that can't auto-apply on tap alone (a number has to be
 * typed first), so it reveals an inline input + its own small Apply
 * action within the same sheet rather than a second modal.
 */

import React, { useState } from "react";
import { ActivityIndicator, Modal, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Check } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

const PRESETS = [3, 5, 10, 15, 20, 25];

interface Props {
  visible: boolean;
  currentValue: number;
  isSubmitting: boolean;
  onApply: (value: number) => void;
  onClose: () => void;
}

export function DefaultThresholdSheet({ visible, currentValue, isSubmitting, onApply, onClose }: Props) {
  const theme = useTheme();
  const [customOpen, setCustomOpen] = useState(false);
  const [customText, setCustomText] = useState("");

  const isCurrentAPreset = PRESETS.includes(currentValue);

  const applyPreset = (value: number) => {
    onApply(value);
    onClose();
  };

  const applyCustom = () => {
    const parsed = Number.parseInt(customText, 10);
    if (!Number.isFinite(parsed) || parsed < 0) return;
    onApply(parsed);
    setCustomOpen(false);
    setCustomText("");
    onClose();
  };

  return (
    <Modal visible={visible} animationType="fade" transparent onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable style={[styles.sheet, { backgroundColor: theme.colors.background }]} onPress={() => {}}>
          <Text style={[styles.title, { color: theme.colors.onSurface }]}>Default Low Stock Threshold</Text>
          <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>
            New products start with this threshold.
          </Text>

          {PRESETS.map((value) => {
            const isSelected = currentValue === value;
            return (
              <Pressable
                key={value}
                onPress={() => applyPreset(value)}
                style={styles.row}
                accessibilityRole="radio"
                accessibilityState={{ checked: isSelected }}
              >
                <Text style={[styles.rowLabel, { color: theme.colors.onSurface }]}>{value} units</Text>
                {isSelected && <Check size={18} color={theme.colors.primary} strokeWidth={2.5} />}
              </Pressable>
            );
          })}

          <Pressable
            onPress={() => setCustomOpen((open) => !open)}
            style={styles.row}
            accessibilityRole="radio"
            accessibilityState={{ checked: !isCurrentAPreset }}
          >
            <Text style={[styles.rowLabel, { color: theme.colors.onSurface }]}>Custom</Text>
            {!isCurrentAPreset && <Check size={18} color={theme.colors.primary} strokeWidth={2.5} />}
          </Pressable>

          {customOpen && (
            <View style={styles.customRow}>
              <TextInput
                value={customText}
                onChangeText={setCustomText}
                placeholder={!isCurrentAPreset ? String(currentValue) : "e.g. 12"}
                placeholderTextColor={theme.colors.onSurfaceVariant}
                keyboardType="number-pad"
                style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
                accessibilityLabel="Custom threshold"
              />
              <Pressable
                onPress={applyCustom}
                disabled={isSubmitting || customText.trim() === ""}
                style={[
                  styles.applyButton,
                  { backgroundColor: customText.trim() ? theme.colors.primary : theme.colors.surfaceDisabled },
                ]}
                accessibilityRole="button"
                accessibilityLabel="Apply"
              >
                {isSubmitting ? (
                  <ActivityIndicator color={theme.colors.onPrimary} />
                ) : (
                  <Text
                    style={[
                      styles.applyButtonText,
                      { color: customText.trim() ? theme.colors.onPrimary : theme.colors.onSurfaceDisabled },
                    ]}
                  >
                    Apply
                  </Text>
                )}
              </Pressable>
            </View>
          )}
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.4)", justifyContent: "flex-end" },
  sheet: { borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg, padding: spacing.lg, gap: spacing.xs },
  title: { ...typography.h2, fontWeight: "700" },
  hint: { ...typography.bodySmall, marginBottom: spacing.sm },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    minHeight: 48,
    paddingVertical: spacing.sm,
  },
  rowLabel: { ...typography.body },
  customRow: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.sm, alignItems: "center" },
  input: {
    flex: 1,
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    minHeight: 44,
    ...typography.body,
  },
  applyButton: {
    minHeight: 44,
    paddingHorizontal: spacing.lg,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radius.md,
  },
  applyButtonText: { ...typography.bodySmall, fontWeight: "700" },
});
