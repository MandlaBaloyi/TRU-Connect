/**
 * BulkDiscountModal — a single percentage input, matching
 * BulkPriceModal's own visual language (same sheet/backdrop/button
 * styling) but genuinely simpler: there's only one real input here,
 * unlike price adjustment's direction+type+value.
 *
 * SETS compare_at_price, NEVER TOUCHES price -- the real point of
 * this whole feature (see product_service.py's own bulk_set_discount
 * docstring): a supplier puts products on sale by percentage without
 * doing the "what number do I actually type" math themselves, and
 * without accidentally changing what anything actually sells for.
 *
 * 1-99 ONLY -- mirrors the real backend's own validation exactly (0
 * isn't a real discount; 100+ divides by zero or goes negative). The
 * backend re-validates this regardless (this app never trusts a
 * client-side check as the real gate), but catching it here means a
 * supplier sees the problem immediately, before a round trip.
 */

import React, { useState } from "react";
import { ActivityIndicator, Modal, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useTheme } from "react-native-paper";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  visible: boolean;
  selectedCount: number;
  isSubmitting: boolean;
  onApply: (discountPercent: number) => void;
  onClose: () => void;
}

export function BulkDiscountModal({ visible, selectedCount, isSubmitting, onApply, onClose }: Props) {
  const theme = useTheme();
  const [valueText, setValueText] = useState("");

  const discountPercent = Number.parseInt(valueText, 10);
  const isValid = valueText.trim() !== "" && Number.isFinite(discountPercent) && discountPercent > 0 && discountPercent < 100;

  const handleApply = () => {
    if (!isValid) return;
    onApply(discountPercent);
  };

  const summary =
    isValid &&
    `Sets a "was" price on ${selectedCount} ${selectedCount === 1 ? "product" : "products"} so each shows ${valueText}% off -- the actual selling price is never changed.`;

  return (
    <Modal visible={visible} animationType="fade" transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={[styles.sheet, { backgroundColor: theme.colors.background }]}>
          <Text style={[styles.title, { color: theme.colors.onSurface }]}>
            Set discount for {selectedCount} {selectedCount === 1 ? "product" : "products"}
          </Text>

          <TextInput
            value={valueText}
            onChangeText={setValueText}
            placeholder="20"
            placeholderTextColor={theme.colors.onSurfaceVariant}
            keyboardType="number-pad"
            style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            accessibilityLabel="Discount percentage"
          />
          <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>
            A whole number between 1 and 99, e.g. 20 for "20% off".
          </Text>

          {summary && <Text style={[styles.summary, { color: theme.colors.onSurfaceVariant }]}>{summary}</Text>}

          <View style={styles.buttonRow}>
            <Pressable onPress={onClose} style={styles.secondaryButton} accessibilityRole="button" accessibilityLabel="Cancel">
              <Text style={[styles.secondaryButtonText, { color: theme.colors.onSurfaceVariant }]}>Cancel</Text>
            </Pressable>
            <Pressable
              onPress={handleApply}
              disabled={!isValid || isSubmitting}
              style={[
                styles.primaryButton,
                { backgroundColor: isValid ? theme.colors.primary : theme.colors.surfaceDisabled },
              ]}
              accessibilityRole="button"
              accessibilityLabel="Apply"
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
                  Apply
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
  sheet: {
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    padding: spacing.lg,
    gap: spacing.md,
  },
  title: { ...typography.h2, fontWeight: "700" },
  input: { borderWidth: 1, borderRadius: radius.md, paddingHorizontal: spacing.md, minHeight: 48, ...typography.body },
  hint: { ...typography.caption },
  summary: { ...typography.bodySmall },
  buttonRow: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.xs },
  secondaryButton: { flex: 1, minHeight: 48, alignItems: "center", justifyContent: "center" },
  secondaryButtonText: { ...typography.body, fontWeight: "600" },
  primaryButton: { flex: 1, minHeight: 48, alignItems: "center", justifyContent: "center", borderRadius: radius.md },
  primaryButtonText: { ...typography.body, fontWeight: "700" },
});
