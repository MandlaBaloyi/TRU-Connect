import React from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Package } from "lucide-react-native";

import type { InventoryListItem } from "../types";
import { InventoryStatusBadge } from "./InventoryStatusBadge";
import { calculateDiscount } from "../../products/algorithms/discount";
import { formatCents } from "../../products/services/productMapper";
import { UNIT_OPTIONS } from "../../products/types";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  item: InventoryListItem;
  onPress: () => void;
}

function unitLabel(value: InventoryListItem["product"]["sellingUnit"]): string {
  return UNIT_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function InventoryListRow({ item, onPress }: Props) {
  const theme = useTheme();
  const { product, availableQuantity, status } = item;
  const discount = calculateDiscount(product.priceCents, product.compareAtPriceCents);

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.row, pressed && styles.pressed]}
      accessibilityRole="button"
      accessibilityLabel={`${product.name}, ${availableQuantity} available, ${status.replace("_", " ").toLowerCase()}`}
    >
      <View style={[styles.thumb, { backgroundColor: theme.colors.surfaceVariant }]}>
        {product.images.length > 0 ? (
          <Image source={{ uri: product.images[0] }} style={styles.thumbImage} />
        ) : (
          <Package size={20} color={theme.colors.onSurfaceVariant} strokeWidth={1.75} />
        )}
        {discount && (
          <View style={[styles.saleBadge, { backgroundColor: theme.colors.error }]}>
            <Text style={styles.saleBadgeText}>{discount.percentOff}% OFF</Text>
          </View>
        )}
      </View>

      <View style={styles.body}>
        <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={1}>
          {product.name}
        </Text>
        <View style={styles.priceRow}>
          <Text style={[styles.price, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
            {formatCents(product.priceCents)} / {unitLabel(product.sellingUnit)}
          </Text>
          {product.compareAtPriceCents !== null && (
            <Text style={[styles.compareAtPrice, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
              {formatCents(product.compareAtPriceCents)}
            </Text>
          )}
        </View>
        <View style={styles.metaRow}>
          <Text style={[styles.available, { color: theme.colors.onSurface }]}>{availableQuantity} available</Text>
          <Text style={{ color: theme.colors.onSurfaceVariant }}>•</Text>
          <InventoryStatusBadge status={status} />
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: spacing.md, paddingVertical: spacing.sm, minHeight: 44 },
  pressed: { opacity: 0.7 },
  thumb: {
    width: 48,
    height: 48,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
  },
  thumbImage: { width: "100%", height: "100%" },
  saleBadge: {
    position: "absolute",
    bottom: 2,
    left: 2,
    right: 2,
    paddingVertical: 1,
    borderRadius: 3,
    alignItems: "center",
  },
  saleBadgeText: { color: "#FFFFFF", fontSize: 8, fontWeight: "700" },
  body: { flex: 1, gap: 2 },
  name: { ...typography.h2 },
  priceRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  price: { ...typography.bodySmall },
  compareAtPrice: { ...typography.bodySmall, textDecorationLine: "line-through" },
  metaRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs, marginTop: 2 },
  available: { ...typography.bodySmall, fontWeight: "700" },
});
