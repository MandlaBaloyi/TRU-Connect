/**
 * SelectionActionBar — replaces the FAB while selection mode is
 * active. "Archive" is hidden when every selected product is already
 * archived (e.g. browsing the Archived filter) -- archiving an
 * already-archived product is a no-op the supplier shouldn't be
 * offered in the first place, matching ProductDetailScreen's own rule
 * of hiding the single-item Archive action there too.
 *
 * onUpdateStock is OPTIONAL -- BulkEditScreen stopped passing it once
 * Products migrated to inventory-derived status (see that screen's own
 * docstring): mutating Product.stockStatus in bulk had no visible
 * effect anymore, so the button was retired rather than left as a
 * control that silently did nothing. Kept optional here, not deleted
 * outright, since a future "Bulk Inventory" (mass stock ADJUSTMENT,
 * not a status toggle) could reasonably reuse this same action bar.
 */

import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Archive, Tag, X } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  selectedCount: number;
  showArchiveAction: boolean;
  onUpdateStock?: () => void;
  onChangePrice: () => void;
  onArchive: () => void;
  onCancel: () => void;
}

export function SelectionActionBar({
  selectedCount,
  showArchiveAction,
  onUpdateStock,
  onChangePrice,
  onArchive,
  onCancel,
}: Props) {
  const theme = useTheme();

  return (
    <View
      style={[styles.bar, { backgroundColor: theme.colors.surface, borderTopColor: theme.colors.outline }]}
    >
      <View style={styles.header}>
        <Text style={[styles.count, { color: theme.colors.onSurface }]}>
          {selectedCount} selected
        </Text>
        <Pressable onPress={onCancel} hitSlop={12} accessibilityRole="button" accessibilityLabel="Cancel selection">
          <X size={20} color={theme.colors.onSurfaceVariant} />
        </Pressable>
      </View>

      <View style={styles.actions}>
        {onUpdateStock && (
          <Pressable
            onPress={onUpdateStock}
            disabled={selectedCount === 0}
            style={[styles.action, { borderColor: theme.colors.outline }]}
            accessibilityRole="button"
            accessibilityLabel="Update stock"
          >
            <Text style={[styles.actionText, { color: theme.colors.onSurface }]}>Update Stock</Text>
          </Pressable>
        )}
        <Pressable
          onPress={onChangePrice}
          disabled={selectedCount === 0}
          style={[styles.action, { borderColor: theme.colors.outline }]}
          accessibilityRole="button"
          accessibilityLabel="Change price"
        >
          <Tag size={14} color={theme.colors.onSurface} strokeWidth={2} />
          <Text style={[styles.actionText, { color: theme.colors.onSurface }]}>Change Price</Text>
        </Pressable>
        {showArchiveAction && (
          <Pressable
            onPress={onArchive}
            disabled={selectedCount === 0}
            style={[styles.action, { borderColor: theme.colors.error }]}
            accessibilityRole="button"
            accessibilityLabel="Archive"
          >
            <Archive size={14} color={theme.colors.error} strokeWidth={2} />
            <Text style={[styles.actionText, { color: theme.colors.error }]}>Archive</Text>
          </Pressable>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    paddingBottom: spacing.lg,
    gap: spacing.sm,
  },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  count: { ...typography.body, fontWeight: "700" },
  actions: { flexDirection: "row", gap: spacing.sm },
  action: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    minHeight: 44,
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.sm,
  },
  actionText: { ...typography.bodySmall, fontWeight: "600" },
});
