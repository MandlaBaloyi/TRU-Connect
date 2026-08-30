import React from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Minus, Plus, Trash2 } from "lucide-react-native";

import { formatCents } from "../../../supplier/products/services/productMapper";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { CartItem } from "../types";

interface Props {
  item: CartItem;
  onPress: () => void;
  onIncrement: () => void;
  onDecrement: () => void;
  onRemove: () => void;
  isBusy: boolean;
}

/**
 * One cart row -- thumbnail, name, price, and the same real trash/
 * quantity/plus stepper as the Bash reference. Decrementing to 1 and
 * pressing minus again removes the item entirely (matches how most
 * real carts behave: there's no meaningful "quantity 0" state sitting
 * in a cart, either you have some or you don't).
 *
 * A stale item (its product has since been archived or removed by the
 * supplier) shows a clear warning instead of the normal stepper --
 * still visible, never silently dropped, but the only real action
 * left is removing it.
 */
export function CartItemRow({ item, onPress, onIncrement, onDecrement, onRemove, isBusy }: Props) {
  const theme = useTheme();
  const photoUrl = item.images[0] ?? null;

  return (
    <View style={styles.row}>
      <Pressable
        style={styles.tappableArea}
        onPress={onPress}
        accessibilityRole="button"
        accessibilityLabel={`View ${item.productName}`}
      >
        <View style={[styles.imageWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
          {photoUrl && <Image source={{ uri: photoUrl }} style={styles.image} resizeMode="contain" />}
        </View>

        <View style={styles.details}>
          <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={2}>
            {item.productName}
          </Text>
          <Text style={[styles.price, { color: theme.colors.onSurface }]}>{formatCents(item.priceCentsAtAddTime)}</Text>
        </View>
      </Pressable>

      <View style={styles.actionsColumn}>
        {item.isStale ? (
          <View style={styles.staleRow}>
            <Text style={[styles.staleText, { color: theme.colors.error }]}>No longer available</Text>
            <Pressable onPress={onRemove} disabled={isBusy} accessibilityRole="button" accessibilityLabel="Remove">
              <Text style={[styles.removeLink, { color: theme.colors.error }]}>Remove</Text>
            </Pressable>
          </View>
        ) : (
          <View style={[styles.stepper, { borderColor: theme.colors.outline }]}>
            <Pressable
              onPress={item.quantity <= 1 ? onRemove : onDecrement}
              disabled={isBusy}
              hitSlop={8}
              style={styles.stepperButton}
              accessibilityRole="button"
              accessibilityLabel={item.quantity <= 1 ? "Remove" : "Decrease quantity"}
            >
              {item.quantity <= 1 ? (
                <Trash2 size={16} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
              ) : (
                <Minus size={16} color={theme.colors.onSurfaceVariant} strokeWidth={2.5} />
              )}
            </Pressable>
            <Text style={[styles.stepperValue, { color: theme.colors.onSurface }]}>{item.quantity}</Text>
            <Pressable
              onPress={onIncrement}
              disabled={isBusy}
              hitSlop={8}
              style={styles.stepperButton}
              accessibilityRole="button"
              accessibilityLabel="Increase quantity"
            >
              <Plus size={16} color={theme.colors.onSurfaceVariant} strokeWidth={2.5} />
            </Pressable>
          </View>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "flex-start", gap: spacing.sm, paddingVertical: spacing.sm },
  tappableArea: { flex: 1, flexDirection: "row", gap: spacing.sm },
  imageWrap: { width: 72, height: 72, borderRadius: radius.md, alignItems: "center", justifyContent: "center", overflow: "hidden" },
  image: { width: "100%", height: "100%" },
  details: { flex: 1, gap: 4, justifyContent: "center" },
  name: { ...typography.body, fontWeight: "700" },
  price: { ...typography.body, fontWeight: "700" },
  actionsColumn: { justifyContent: "center" },
  staleRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  staleText: { ...typography.bodySmall, fontWeight: "600" },
  removeLink: { ...typography.bodySmall, fontWeight: "700", textDecorationLine: "underline" },
  stepper: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: radius.pill,
  },
  stepperButton: { paddingHorizontal: spacing.sm, paddingVertical: spacing.xs },
  stepperValue: { ...typography.body, fontWeight: "700", minWidth: 24, textAlign: "center" },
});
