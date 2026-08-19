import React from "react";
import { Modal, Pressable, StyleSheet, Text } from "react-native";
import { useTheme } from "react-native-paper";
import { Check } from "lucide-react-native";

import { SORT_OPTIONS } from "../types";
import type { SortOption } from "../types";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  visible: boolean;
  selected: SortOption;
  onSelect: (option: SortOption) => void;
  onClose: () => void;
}

export function SortOptionsSheet({ visible, selected, onSelect, onClose }: Props) {
  const theme = useTheme();

  return (
    <Modal visible={visible} animationType="fade" transparent onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable style={[styles.sheet, { backgroundColor: theme.colors.background }]} onPress={() => {}}>
          <Text style={[styles.title, { color: theme.colors.onSurface }]}>Sort by</Text>
          {SORT_OPTIONS.map((option) => {
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
