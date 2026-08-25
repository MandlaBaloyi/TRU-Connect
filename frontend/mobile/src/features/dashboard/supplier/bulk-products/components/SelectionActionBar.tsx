/**
 * SelectionActionBar — replaces the FAB while selection mode is
 * active. Which actions show is driven by `mode`, set by the CALLING
 * SCREEN from whichever filter tab is currently active -- not derived
 * from the selected products' own archived state, since selectedIds
 * doesn't clear when the filter tab changes (a supplier could select
 * on "All", then switch to "Archived" with that old selection still
 * technically held). Matching the actual tab you're looking at is the
 * more predictable, intuitive rule: on the Archived tab, you always
 * see Unarchive + Delete; everywhere else, Change Price + (conditional)
 * Archive, unchanged from before.
 *
 * "Archive" is still hidden when every selected product is already
 * archived -- archiving an already-archived product is a no-op the
 * supplier shouldn't be offered, matching ProductDetailScreen's own
 * rule for the single-item Archive action.
 *
 * onUpdateStock is OPTIONAL -- see this file's own git history /
 * BulkEditScreen's own docstring for why (retired once Products
 * migrated to inventory-derived status). Kept optional, not deleted,
 * since a future "Bulk Inventory" could reasonably reuse this bar.
 *
 * Delete has NO confirmation built into this component -- it fires
 * onDelete the moment it's pressed. Confirmation is the CALLER's job
 * (BulkEditScreen wraps onDelete in a real Alert.alert before calling
 * the mutation), same separation as every other destructive action in
 * this app: the action bar is dumb UI, the screen owns the decision
 * of when something is scary enough to double-check.
 */

import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Archive, ArchiveRestore, Percent, Tag, Trash2, X } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  selectedCount: number;
  mode: "ACTIVE" | "ARCHIVED";
  showArchiveAction: boolean;
  onUpdateStock?: () => void;
  onChangePrice: () => void;
  onSetDiscount: () => void;
  onArchive: () => void;
  onUnarchive: () => void;
  onDelete: () => void;
  onCancel: () => void;
}

export function SelectionActionBar({
  selectedCount,
  mode,
  showArchiveAction,
  onUpdateStock,
  onChangePrice,
  onSetDiscount,
  onArchive,
  onUnarchive,
  onDelete,
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
        {mode === "ARCHIVED" ? (
          <>
            <Pressable
              onPress={onUnarchive}
              disabled={selectedCount === 0}
              style={[styles.action, { borderColor: theme.colors.outline }]}
              accessibilityRole="button"
              accessibilityLabel="Unarchive"
            >
              <ArchiveRestore size={14} color={theme.colors.onSurface} strokeWidth={2} />
              <Text style={[styles.actionText, { color: theme.colors.onSurface }]}>Unarchive</Text>
            </Pressable>
            <Pressable
              onPress={onDelete}
              disabled={selectedCount === 0}
              style={[styles.action, { borderColor: theme.colors.error }]}
              accessibilityRole="button"
              accessibilityLabel="Delete"
            >
              <Trash2 size={14} color={theme.colors.error} strokeWidth={2} />
              <Text style={[styles.actionText, { color: theme.colors.error }]}>Delete</Text>
            </Pressable>
          </>
        ) : (
          <>
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
            <Pressable
              onPress={onSetDiscount}
              disabled={selectedCount === 0}
              style={[styles.action, { borderColor: theme.colors.outline }]}
              accessibilityRole="button"
              accessibilityLabel="Set discount"
            >
              <Percent size={14} color={theme.colors.onSurface} strokeWidth={2} />
              <Text style={[styles.actionText, { color: theme.colors.onSurface }]}>Set Discount</Text>
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
          </>
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
