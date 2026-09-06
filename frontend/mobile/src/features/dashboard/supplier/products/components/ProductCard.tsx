/**
 * ProductCard — one product in the compact vertical list, matching the
 * approved mockup exactly: thumbnail, name, "price • stock status" on
 * one line, nothing else. Category/description deliberately don't
 * appear here -- they belong on a future product-detail/edit screen,
 * not the list a supplier scans to manage 25+ products quickly.
 *
 * STATUS NOW COMES FROM THE CALLER, NOT product.stockStatus --
 * Inventory (a separate feature) computes real stock status from
 * quantity now; this card never reads Product's own legacy field (see
 * products/types.ts's own Product.stockStatus docstring for the full
 * reasoning). `inventoryStatus` is a TYPE-ONLY import from inventory/
 * types (erased at compile time, so this doesn't create a runtime
 * dependency between the two features' data layers -- only their UI
 * layers, which is one-directional and safe). Callers
 * (ProductsScreen, BulkEditScreen) fetch inventory data themselves and
 * pass the resolved status down; while it's still loading, this card
 * simply shows no badge rather than a stale/wrong one.
 */

import React from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Archive, Check, Package, Pin } from "lucide-react-native";

import type { Product } from "../types";
import type { InventoryStatus } from "../../inventory/types";
import { calculateDiscount } from "../algorithms/discount";
import { formatCents } from "../services/productMapper";
import { InventoryStatusBadge } from "../../inventory/components";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  product: Product;
  /** Undefined while the caller's own inventory fetch is still
   *  loading -- shows no badge rather than guessing. */
  inventoryStatus?: InventoryStatus;
  onPress?: () => void;
  onLongPress?: () => void;
  /** Selection-mode UI: renders a checkbox and swaps the accessibility
   *  role, but the SELECTION STATE itself lives entirely in the parent
   *  (ProductsScreen) -- this component never decides what a tap does,
   *  it only reflects `selected` and calls `onPress`. */
  selectable?: boolean;
  selected?: boolean;
  /** Featured on the supplier's business profile — shows a small pin
   *  in the meta row. */
  pinned?: boolean;
  /** Right-aligned slot, e.g. the ⋮ pin menu. Not shown in selection
   *  mode. */
  trailing?: React.ReactNode;
}

export function ProductCard({
  product,
  inventoryStatus,
  onPress,
  onLongPress,
  selectable = false,
  selected = false,
  pinned = false,
  trailing,
}: Props) {
  const theme = useTheme();
  const interactive = Boolean(onPress) || selectable;
  const discount = calculateDiscount(product.priceCents, product.compareAtPriceCents);

  return (
    <Pressable
      onPress={onPress}
      onLongPress={onLongPress}
      disabled={!interactive}
      style={({ pressed }) => [
        styles.card,
        product.isArchived && styles.archived,
        interactive && pressed && styles.pressed,
      ]}
      accessibilityRole={selectable ? "checkbox" : interactive ? "button" : "text"}
      accessibilityState={selectable ? { checked: selected } : undefined}
      accessibilityLabel={`${product.name}, ${formatCents(product.priceCents)}${
        product.isArchived ? ", archived" : inventoryStatus ? `, ${inventoryStatus.replace("_", " ").toLowerCase()}` : ""
      }`}
    >
      {selectable && (
        <View
          style={[
            styles.checkbox,
            { borderColor: selected ? theme.colors.primary : theme.colors.outline },
            selected && { backgroundColor: theme.colors.primary },
          ]}
        >
          {selected && <Check size={14} color={theme.colors.onPrimary} strokeWidth={3} />}
        </View>
      )}

      <View style={[styles.thumb, { backgroundColor: theme.colors.surfaceVariant }]}>
        {product.images.length > 0 ? (
          <Image source={{ uri: product.images[0] }} style={styles.thumbImage} />
        ) : (
          <Package size={22} color={theme.colors.onSurfaceVariant} strokeWidth={1.75} />
        )}
        {discount && (
          <View style={[styles.saleBadge, { backgroundColor: theme.colors.error }]}>
            <Text style={styles.saleBadgeText}>{discount.percentOff}% OFF</Text>
          </View>
        )}
      </View>

      <View style={styles.body}>
        <View style={styles.nameRow}>
          <Text style={[styles.name, { color: theme.colors.onSurface }]} numberOfLines={1}>
            {product.name}
          </Text>
          {pinned && <Pin size={13} color={theme.colors.primary} strokeWidth={2.4} />}
        </View>
        <View style={styles.metaRow}>
          <Text style={[styles.price, { color: theme.colors.onSurface }]} numberOfLines={1}>
            {formatCents(product.priceCents)}
          </Text>
          {product.compareAtPriceCents !== null && (
            <Text style={[styles.compareAtPrice, { color: theme.colors.onSurfaceVariant }]} numberOfLines={1}>
              {formatCents(product.compareAtPriceCents)}
            </Text>
          )}
          {(product.isArchived || inventoryStatus) && <Text style={{ color: theme.colors.onSurfaceVariant }}>•</Text>}
          {product.isArchived ? (
            <View style={styles.archivedBadge}>
              <Archive size={11} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
              <Text style={[styles.archivedLabel, { color: theme.colors.onSurfaceVariant }]}>Archived</Text>
            </View>
          ) : (
            inventoryStatus && <InventoryStatusBadge status={inventoryStatus} />
          )}
        </View>
      </View>

      {!selectable && trailing}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    paddingVertical: spacing.sm,
    minHeight: 44,
  },
  archived: { opacity: 0.6 },
  pressed: { opacity: 0.7 },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 2,
    alignItems: "center",
    justifyContent: "center",
  },
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
  body: { flex: 1, gap: 4 },
  nameRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  name: { ...typography.h2, flexShrink: 1 },
  metaRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  price: { ...typography.body, fontWeight: "700" },
  compareAtPrice: { ...typography.bodySmall, textDecorationLine: "line-through" },
  archivedBadge: { flexDirection: "row", alignItems: "center", gap: 4 },
  archivedLabel: { ...typography.bodySmall },
});
