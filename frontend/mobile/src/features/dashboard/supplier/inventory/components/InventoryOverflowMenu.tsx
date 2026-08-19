/**
 * InventoryOverflowMenu — same spec as Products' own
 * ProductsOverflowMenu (which see for the "why this exact size/weight"
 * reasoning): strokeWidth 2.4, same iconButton touch target, so every
 * "⋮" in this app reads as the same control.
 */

import React, { useState } from "react";
import { Pressable, StyleSheet } from "react-native";
import { Menu, useTheme } from "react-native-paper";
import { AlertTriangle, Download, MoreVertical, SlidersHorizontal } from "lucide-react-native";

import { spacing } from "@/theme/spacing";

interface Props {
  onExport: () => void;
  onEditDefaultThreshold: () => void;
  onEditAlertChannel: () => void;
}

export function InventoryOverflowMenu({ onExport, onEditDefaultThreshold, onEditAlertChannel }: Props) {
  const theme = useTheme();
  const [visible, setVisible] = useState(false);

  const runAndClose = (action: () => void) => {
    setVisible(false);
    action();
  };

  return (
    <Menu
      visible={visible}
      onDismiss={() => setVisible(false)}
      anchor={
        <Pressable
          onPress={() => setVisible(true)}
          hitSlop={10}
          style={styles.iconButton}
          accessibilityRole="button"
          accessibilityLabel="More options"
        >
          <MoreVertical size={20} color={theme.colors.onSurface} strokeWidth={2.4} />
        </Pressable>
      }
    >
      <Menu.Item
        onPress={() => runAndClose(onExport)}
        title="Export Inventory"
        leadingIcon={({ size, color }) => <Download size={size} color={color} strokeWidth={2} />}
      />
      <Menu.Item
        onPress={() => runAndClose(onEditDefaultThreshold)}
        title="Default Low Stock Threshold"
        leadingIcon={({ size, color }) => <SlidersHorizontal size={size} color={color} strokeWidth={2} />}
      />
      <Menu.Item
        onPress={() => runAndClose(onEditAlertChannel)}
        title="Low Stock Alerts"
        leadingIcon={({ size, color }) => <AlertTriangle size={size} color={color} strokeWidth={2} />}
      />
    </Menu>
  );
}

const styles = StyleSheet.create({
  iconButton: { padding: spacing.xs, marginLeft: spacing.xs },
});
