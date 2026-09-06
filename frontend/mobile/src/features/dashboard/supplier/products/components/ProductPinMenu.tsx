/**
 * ProductPinMenu — the "⋮" on a product row in the Products list. One
 * item: feature this product on the supplier's business profile, or
 * remove it. Owns its own open/closed state (same pattern as
 * ProductsOverflowMenu). A rejected pin (max 6, or an archived
 * product) is shown as a plain alert.
 *
 * Kept as its own tiny component rather than inline in ProductCard so
 * the card stays a pure presentational row and BulkEditScreen's own
 * use of it is unaffected.
 */
import React, { useState } from "react";
import { Alert, Pressable, StyleSheet } from "react-native";
import { Menu, useTheme } from "react-native-paper";
import { MoreVertical, Pin, PinOff } from "lucide-react-native";

import { spacing } from "@/theme/spacing";
import { useTogglePin } from "../hooks/useTogglePin";

interface Props {
  productId: string;
  isPinned: boolean;
  /** Archived products can't be featured — the menu still opens, but
   *  the pin item is disabled with a hint. */
  disabled?: boolean;
}

export function ProductPinMenu({ productId, isPinned, disabled = false }: Props) {
  const theme = useTheme();
  const [visible, setVisible] = useState(false);
  const { togglePin, isToggling } = useTogglePin();

  const run = async () => {
    setVisible(false);
    try {
      await togglePin({ productId, pinned: !isPinned });
    } catch (e) {
      Alert.alert(
        isPinned ? "Couldn't remove from profile" : "Couldn't feature this product",
        e instanceof Error ? e.message : "Please try again."
      );
    }
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
          accessibilityLabel="Product options"
        >
          <MoreVertical size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2.4} />
        </Pressable>
      }
    >
      <Menu.Item
        onPress={run}
        disabled={disabled || isToggling}
        title={isPinned ? "Remove from business profile" : "Feature on business profile"}
        leadingIcon={({ size, color }) =>
          isPinned ? (
            <PinOff size={size} color={color} strokeWidth={2} />
          ) : (
            <Pin size={size} color={color} strokeWidth={2} />
          )
        }
      />
    </Menu>
  );
}

const styles = StyleSheet.create({
  iconButton: { padding: spacing.xs },
});
