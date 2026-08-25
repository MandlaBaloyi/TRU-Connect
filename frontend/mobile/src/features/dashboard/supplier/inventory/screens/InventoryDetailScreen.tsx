/**
 * InventoryDetailScreen — on hand / reserved / available / low-stock
 * threshold for one product. "Adjust Stock" is the primary action, per
 * the design notes' own framing -- suppliers think in terms of what
 * changed ("received 5 cases"), not retyping an absolute number.
 * Reserved is always 0 today (see types.ts's own docstring: no Orders
 * to reserve against yet) but shown anyway, since the field existing
 * and reading 0 is more honest than hiding it only to add it back
 * later.
 */

import React, { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Pencil } from "lucide-react-native";

import { useInventoryItem, useSetLowStockThreshold } from "../hooks";
import { InventoryStatusBadge, ThresholdModal } from "../components";
import { formatCents } from "../../products/services/productMapper";
import { UNIT_OPTIONS } from "../../products/types";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

function unitLabel(value: string): string {
  return UNIT_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export default function InventoryDetailScreen() {
  const { productId } = useLocalSearchParams<{ productId: string }>();
  const router = useRouter();
  const theme = useTheme();

  const { item, isLoading, isError, refetch } = useInventoryItem(productId ?? "");
  const { setLowStockThreshold, isSettingThreshold } = useSetLowStockThreshold();
  const [thresholdModalOpen, setThresholdModalOpen] = useState(false);

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

  const { product, inventory, status, availableQuantity } = item;
  const unit = unitLabel(product.sellingUnit);

  const handleSaveThreshold = async (value: number) => {
    await setLowStockThreshold({ productId: product.id, lowStockThreshold: value });
    setThresholdModalOpen(false);
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.titleBlock}>
          <Text style={[styles.name, { color: theme.colors.onSurface }]}>{product.name}</Text>
          <Text style={[styles.productCode, { color: theme.colors.onSurfaceVariant }]}>{product.productCode}</Text>
          <Text style={[styles.price, { color: theme.colors.onSurfaceVariant }]}>
            {formatCents(product.priceCents)} / {unit}
          </Text>
          <InventoryStatusBadge status={status} />
        </View>

        <View style={[styles.card, { borderColor: theme.colors.outline }]}>
          <View style={styles.row}>
            <Text style={[styles.rowLabel, { color: theme.colors.onSurfaceVariant }]}>On hand</Text>
            <Text style={[styles.rowValue, { color: theme.colors.onSurface }]}>
              {inventory.quantityOnHand} {unit.toLowerCase()}
            </Text>
          </View>
          <View style={[styles.divider, { backgroundColor: theme.colors.outline }]} />
          <View style={styles.row}>
            <Text style={[styles.rowLabel, { color: theme.colors.onSurfaceVariant }]}>Reserved</Text>
            <Text style={[styles.rowValue, { color: theme.colors.onSurface }]}>
              {inventory.quantityReserved} {unit.toLowerCase()}
            </Text>
          </View>
          <View style={[styles.divider, { backgroundColor: theme.colors.outline }]} />
          <View style={styles.row}>
            <Text style={[styles.rowLabel, { color: theme.colors.onSurfaceVariant }]}>Available</Text>
            <Text style={[styles.rowValueEmphasis, { color: theme.colors.primary }]}>
              {availableQuantity} {unit.toLowerCase()}
            </Text>
          </View>
          <View style={[styles.divider, { backgroundColor: theme.colors.outline }]} />
          <Pressable onPress={() => setThresholdModalOpen(true)} style={styles.row} accessibilityRole="button">
            <Text style={[styles.rowLabel, { color: theme.colors.onSurfaceVariant }]}>Low stock at</Text>
            <View style={styles.thresholdValue}>
              <Text style={[styles.rowValue, { color: theme.colors.onSurface }]}>
                {inventory.lowStockThreshold} {unit.toLowerCase()}
              </Text>
              <Pencil size={14} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
            </View>
          </Pressable>
        </View>

        <Pressable
          onPress={() => router.push(`/supplier/inventory/${product.id}/adjust`)}
          style={[styles.adjustButton, { backgroundColor: theme.colors.primary }]}
          accessibilityRole="button"
          accessibilityLabel="Adjust stock"
        >
          <Text style={[styles.adjustButtonText, { color: theme.colors.onPrimary }]}>Adjust Stock</Text>
        </Pressable>
      </ScrollView>

      <ThresholdModal
        visible={thresholdModalOpen}
        currentValue={inventory.lowStockThreshold}
        unit={unit}
        isSubmitting={isSettingThreshold}
        onSave={handleSaveThreshold}
        onClose={() => setThresholdModalOpen(false)}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  content: { padding: spacing.md, gap: spacing.lg, paddingBottom: spacing.xxl },
  titleBlock: { gap: spacing.xs },
  name: { ...typography.h1 },
  productCode: { ...typography.caption },
  price: { ...typography.body },
  card: { borderWidth: 1, borderRadius: radius.lg, paddingHorizontal: spacing.md },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: spacing.md },
  rowLabel: { ...typography.body },
  rowValue: { ...typography.body, fontWeight: "600" },
  rowValueEmphasis: { ...typography.h2, fontWeight: "800" },
  thresholdValue: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  divider: { height: StyleSheet.hairlineWidth },
  adjustButton: { minHeight: 52, alignItems: "center", justifyContent: "center", borderRadius: radius.md },
  adjustButtonText: { ...typography.h2 },
});
