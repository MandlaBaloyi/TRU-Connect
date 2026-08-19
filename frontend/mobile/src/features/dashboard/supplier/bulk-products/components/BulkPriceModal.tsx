/**
 * BulkPriceModal — direction (increase/decrease), type (percentage/
 * fixed), and a value. Never asks for a single absolute price -- see
 * types.ts's own PriceAdjustment docstring for why. No live per-item
 * preview table (deliberately simple for this pass); the summary line
 * at the bottom states what will happen in plain language before the
 * supplier commits.
 */

import React, { useState } from "react";
import { ActivityIndicator, Modal, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useTheme } from "react-native-paper";

import type { PriceAdjustment, PriceAdjustmentDirection, PriceAdjustmentType } from "../types";
import { parseCentsInput } from "../../products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  visible: boolean;
  selectedCount: number;
  isSubmitting: boolean;
  onApply: (adjustment: PriceAdjustment) => void;
  onClose: () => void;
}

export function BulkPriceModal({ visible, selectedCount, isSubmitting, onApply, onClose }: Props) {
  const theme = useTheme();
  const [direction, setDirection] = useState<PriceAdjustmentDirection>("INCREASE");
  const [type, setType] = useState<PriceAdjustmentType>("PERCENTAGE");
  const [valueText, setValueText] = useState("");

  const percentageValue = type === "PERCENTAGE" ? Number.parseFloat(valueText) : null;
  const fixedCents = type === "FIXED" ? parseCentsInput(valueText) : null;
  const isValid =
    type === "PERCENTAGE"
      ? percentageValue !== null && Number.isFinite(percentageValue) && percentageValue > 0
      : fixedCents !== null && fixedCents > 0;

  const handleApply = () => {
    if (!isValid) return;
    onApply({
      direction,
      type,
      value: type === "PERCENTAGE" ? (percentageValue as number) : (fixedCents as number),
    });
  };

  const summary =
    isValid &&
    `${direction === "INCREASE" ? "Increases" : "Decreases"} the price of ${selectedCount} ${
      selectedCount === 1 ? "product" : "products"
    } by ${type === "PERCENTAGE" ? `${valueText}%` : `R ${valueText}`} each.`;

  return (
    <Modal visible={visible} animationType="fade" transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={[styles.sheet, { backgroundColor: theme.colors.background }]}>
          <Text style={[styles.title, { color: theme.colors.onSurface }]}>
            Change price for {selectedCount} {selectedCount === 1 ? "product" : "products"}
          </Text>

          <View style={styles.chipRow}>
            {(["INCREASE", "DECREASE"] as PriceAdjustmentDirection[]).map((option) => {
              const selected = option === direction;
              return (
                <Pressable
                  key={option}
                  onPress={() => setDirection(option)}
                  style={[
                    styles.chip,
                    { borderColor: theme.colors.outline },
                    selected && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
                  ]}
                  accessibilityRole="button"
                  accessibilityState={{ selected }}
                >
                  <Text style={{ color: selected ? theme.colors.onPrimary : theme.colors.onSurface, fontWeight: "600" }}>
                    {option === "INCREASE" ? "Increase" : "Decrease"}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          <View style={styles.chipRow}>
            {(["PERCENTAGE", "FIXED"] as PriceAdjustmentType[]).map((option) => {
              const selected = option === type;
              return (
                <Pressable
                  key={option}
                  onPress={() => {
                    setType(option);
                    setValueText("");
                  }}
                  style={[
                    styles.chip,
                    { borderColor: theme.colors.outline },
                    selected && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
                  ]}
                  accessibilityRole="button"
                  accessibilityState={{ selected }}
                >
                  <Text style={{ color: selected ? theme.colors.onPrimary : theme.colors.onSurface, fontWeight: "600" }}>
                    {option === "PERCENTAGE" ? "Percentage" : "Fixed amount"}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          <TextInput
            value={valueText}
            onChangeText={setValueText}
            placeholder={type === "PERCENTAGE" ? "10" : "R 2.00"}
            placeholderTextColor={theme.colors.onSurfaceVariant}
            keyboardType="decimal-pad"
            style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            accessibilityLabel={type === "PERCENTAGE" ? "Percentage" : "Fixed amount"}
          />

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
  chipRow: { flexDirection: "row", gap: spacing.sm },
  chip: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 44,
    borderWidth: 1,
    borderRadius: radius.pill,
  },
  input: { borderWidth: 1, borderRadius: radius.md, paddingHorizontal: spacing.md, minHeight: 48, ...typography.body },
  summary: { ...typography.bodySmall },
  buttonRow: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.xs },
  secondaryButton: { flex: 1, minHeight: 48, alignItems: "center", justifyContent: "center" },
  secondaryButtonText: { ...typography.body, fontWeight: "600" },
  primaryButton: { flex: 1, minHeight: 48, alignItems: "center", justifyContent: "center", borderRadius: radius.md },
  primaryButtonText: { ...typography.body, fontWeight: "700" },
});
