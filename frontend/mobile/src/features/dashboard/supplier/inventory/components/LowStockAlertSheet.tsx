/**
 * LowStockAlertSheet — same bottom-sheet structure and interaction as
 * SortOptionsSheet: tap a row, it applies and the sheet closes
 * immediately. No separate "Save" -- this is a single either/or
 * choice, same reasoning as DefaultThresholdSheet's own preset rows.
 *
 * Actually SENDING an alert needs backend notification/email
 * infrastructure that doesn't exist yet -- this only saves the
 * preference (see inventory/types.ts's own InventorySettings
 * docstring).
 */

import React from "react";
import { Modal, Pressable, StyleSheet, Text } from "react-native";
import { useTheme } from "react-native-paper";
import { Check } from "lucide-react-native";

import type { LowStockAlertChannel } from "../types";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

const OPTIONS: { value: LowStockAlertChannel; label: string }[] = [
  { value: "IN_APP", label: "TRU Connect in-app alerts" },
  { value: "EMAIL", label: "Email" },
];

interface Props {
  visible: boolean;
  selected: LowStockAlertChannel;
  onSelect: (channel: LowStockAlertChannel) => void;
  onClose: () => void;
}

export function LowStockAlertSheet({ visible, selected, onSelect, onClose }: Props) {
  const theme = useTheme();

  return (
    <Modal visible={visible} animationType="fade" transparent onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable style={[styles.sheet, { backgroundColor: theme.colors.background }]} onPress={() => {}}>
          <Text style={[styles.title, { color: theme.colors.onSurface }]}>Low Stock Alerts</Text>
          {OPTIONS.map((option) => {
            const isSelected = option.value === selected;
            return (
              <Pressable
                key={option.value}
                onPress={() => {
                  onSelect(option.value);
                  onClose();
                }}
                style={styles.row}
                accessibilityRole="radio"
                accessibilityState={{ checked: isSelected }}
              >
                <Text style={[styles.rowLabel, { color: theme.colors.onSurface }]}>{option.label}</Text>
                {isSelected && <Check size={18} color={theme.colors.primary} strokeWidth={2.5} />}
              </Pressable>
            );
          })}
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.4)", justifyContent: "flex-end" },
  sheet: { borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg, padding: spacing.lg, gap: spacing.xs },
  title: { ...typography.h2, fontWeight: "700", marginBottom: spacing.sm },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    minHeight: 48,
    paddingVertical: spacing.sm,
  },
  rowLabel: { ...typography.body },
});
