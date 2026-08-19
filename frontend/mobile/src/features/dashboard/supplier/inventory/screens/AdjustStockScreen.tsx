/**
 * AdjustStockScreen — "I received another 5 cases," not "I now have
 * 67." Direction toggle (Add/Remove) + amount, rather than expecting a
 * typed minus sign on a number pad; reason is required, matching the
 * design notes' own reasoning that a reason is what eventually makes
 * an inventory_movements audit log meaningful (not built yet, but this
 * screen already collects what it would need).
 */

import React, { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Minus, Plus } from "lucide-react-native";

import { useAdjustStock, useInventoryItem } from "../hooks";
import { STOCK_ADJUSTMENT_REASON_OPTIONS, InventoryError } from "../types";
import type { StockAdjustmentReason } from "../types";
import { UNIT_OPTIONS } from "../../products/types";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

function unitLabel(value: string): string {
  return UNIT_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

type Direction = "ADD" | "REMOVE";

export default function AdjustStockScreen() {
  const { productId } = useLocalSearchParams<{ productId: string }>();
  const router = useRouter();
  const theme = useTheme();

  const { item, isLoading, isError, refetch } = useInventoryItem(productId ?? "");
  const { adjustStock, isAdjusting } = useAdjustStock();

  const [direction, setDirection] = useState<Direction>("ADD");
  const [amountText, setAmountText] = useState("");
  const [reason, setReason] = useState<StockAdjustmentReason | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError || !item) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState message="Couldn't load this product's stock. Check your connection and try again." onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const unit = unitLabel(item.product.sellingUnit);
  const amount = Number.parseInt(amountText, 10);
  const isValidAmount = Number.isFinite(amount) && amount > 0;
  const signedDelta = direction === "ADD" ? amount : -amount;
  const projectedTotal = isValidAmount ? item.inventory.quantityOnHand + signedDelta : item.inventory.quantityOnHand;
  const canSave = isValidAmount && reason !== null && projectedTotal >= 0 && !isAdjusting;

  const handleSave = async () => {
    if (!canSave) return;
    setError(null);
    try {
      await adjustStock({
        productId: item.product.id,
        quantityDelta: signedDelta,
        reason: reason as StockAdjustmentReason,
      });
      router.back();
    } catch (err) {
      if (err instanceof InventoryError) {
        setError(err.message);
      } else {
        setError("Couldn't save this adjustment. Check your connection and try again.");
      }
    }
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.currentBlock}>
          <Text style={[styles.currentLabel, { color: theme.colors.onSurfaceVariant }]}>Current stock</Text>
          <Text style={[styles.currentValue, { color: theme.colors.onSurface }]}>
            {item.inventory.quantityOnHand} {unit.toLowerCase()}
          </Text>
        </View>

        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Adjustment</Text>
          <View style={styles.directionRow}>
            <Pressable
              onPress={() => setDirection("ADD")}
              style={[
                styles.directionChip,
                { borderColor: theme.colors.outline },
                direction === "ADD" && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
              ]}
              accessibilityRole="button"
              accessibilityState={{ selected: direction === "ADD" }}
            >
              <Plus
                size={16}
                color={direction === "ADD" ? theme.colors.onPrimary : theme.colors.onSurface}
                strokeWidth={2.5}
              />
              <Text
                style={{ color: direction === "ADD" ? theme.colors.onPrimary : theme.colors.onSurface, fontWeight: "600" }}
              >
                Add
              </Text>
            </Pressable>
            <Pressable
              onPress={() => setDirection("REMOVE")}
              style={[
                styles.directionChip,
                { borderColor: theme.colors.outline },
                direction === "REMOVE" && { backgroundColor: theme.colors.error, borderColor: theme.colors.error },
              ]}
              accessibilityRole="button"
              accessibilityState={{ selected: direction === "REMOVE" }}
            >
              <Minus
                size={16}
                color={direction === "REMOVE" ? theme.colors.onError : theme.colors.onSurface}
                strokeWidth={2.5}
              />
              <Text
                style={{
                  color: direction === "REMOVE" ? theme.colors.onError : theme.colors.onSurface,
                  fontWeight: "600",
                }}
              >
                Remove
              </Text>
            </Pressable>
          </View>
          <TextInput
            value={amountText}
            onChangeText={setAmountText}
            placeholder="Quantity, e.g. 20"
            placeholderTextColor={theme.colors.onSurfaceVariant}
            keyboardType="number-pad"
            style={[styles.input, { borderColor: theme.colors.outline, color: theme.colors.onSurface }]}
            accessibilityLabel="Adjustment amount"
          />
        </View>

        <View style={styles.field}>
          <Text style={[styles.label, { color: theme.colors.onSurfaceVariant }]}>Reason</Text>
          {STOCK_ADJUSTMENT_REASON_OPTIONS.map((option) => {
            const selected = option.value === reason;
            return (
              <Pressable
                key={option.value}
                onPress={() => setReason(option.value)}
                style={styles.reasonRow}
                accessibilityRole="radio"
                accessibilityState={{ checked: selected }}
              >
                <View
                  style={[
                    styles.radioDot,
                    { borderColor: theme.colors.outline },
                    selected && { borderColor: theme.colors.primary },
                  ]}
                >
                  {selected && <View style={[styles.radioDotFill, { backgroundColor: theme.colors.primary }]} />}
                </View>
                <Text style={{ color: theme.colors.onSurface }}>{option.label}</Text>
              </Pressable>
            );
          })}
        </View>

        {isValidAmount && (
          <View style={[styles.previewBox, { backgroundColor: theme.colors.surfaceVariant }]}>
            <Text style={[styles.previewText, { color: theme.colors.onSurfaceVariant }]}>
              {item.inventory.quantityOnHand} {direction === "ADD" ? "+" : "-"} {amount} ={" "}
              <Text style={{ fontWeight: "700", color: theme.colors.onSurface }}>
                {projectedTotal} {unit.toLowerCase()}
              </Text>
            </Text>
            {projectedTotal < 0 && (
              <Text style={[styles.previewError, { color: theme.colors.error }]}>That would take stock below zero.</Text>
            )}
          </View>
        )}

        {error && <Text style={[styles.error, { color: theme.colors.error }]}>{error}</Text>}

        <Pressable
          onPress={handleSave}
          disabled={!canSave}
          style={[styles.saveButton, { backgroundColor: canSave ? theme.colors.primary : theme.colors.surfaceDisabled }]}
          accessibilityRole="button"
          accessibilityState={{ disabled: !canSave }}
          accessibilityLabel="Save adjustment"
        >
          {isAdjusting ? (
            <ActivityIndicator color={theme.colors.onPrimary} />
          ) : (
            <Text
              style={[styles.saveButtonText, { color: canSave ? theme.colors.onPrimary : theme.colors.onSurfaceDisabled }]}
            >
              Save
            </Text>
          )}
        </Pressable>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  content: { padding: spacing.md, gap: spacing.lg, paddingBottom: spacing.xxl },
  currentBlock: { alignItems: "center", gap: 2 },
  currentLabel: { ...typography.bodySmall },
  currentValue: { ...typography.display },
  field: { gap: spacing.sm },
  label: { ...typography.bodySmall },
  directionRow: { flexDirection: "row", gap: spacing.sm },
  directionChip: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    minHeight: 44,
    borderWidth: 1,
    borderRadius: radius.md,
  },
  input: { borderWidth: 1, borderRadius: radius.md, paddingHorizontal: spacing.md, minHeight: 48, ...typography.body },
  reasonRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm, minHeight: 44 },
  radioDot: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    alignItems: "center",
    justifyContent: "center",
  },
  radioDotFill: { width: 10, height: 10, borderRadius: 5 },
  previewBox: { borderRadius: radius.md, padding: spacing.md, gap: 4 },
  previewText: { ...typography.body },
  previewError: { ...typography.bodySmall, fontWeight: "600" },
  error: { ...typography.bodySmall },
  saveButton: { minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radius.md },
  saveButtonText: { ...typography.h2 },
});
