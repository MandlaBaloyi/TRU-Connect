import React, { useState } from "react";
import { Pressable, StyleSheet } from "react-native";
import { Menu, useTheme } from "react-native-paper";
import { History, MoreVertical, Trash2 } from "lucide-react-native";

import { spacing } from "@/theme/spacing";

interface Props {
  onOrderHistory: () => void;
  onClearCart: () => void;
}

/**
 * The cart screen's own "⋮" -- mirrors ProductDetailMenu.tsx's own
 * self-contained Menu+anchor-Pressable shape. Two items: Order
 * History (this supplier's own submitted orders, for reference) and
 * Clear Cart (a real, destructive action -- always confirmed before
 * it commits, same discipline as Disconnect's own confirm-first
 * pattern, never fired straight from this menu tap).
 */
export function CartMenu({ onOrderHistory, onClearCart }: Props) {
  const theme = useTheme();
  const [visible, setVisible] = useState(false);

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
        onPress={() => {
          setVisible(false);
          onOrderHistory();
        }}
        title="Order History"
        leadingIcon={() => <History size={20} color={theme.colors.onSurface} strokeWidth={2} />}
      />
      <Menu.Item
        onPress={() => {
          setVisible(false);
          onClearCart();
        }}
        title="Clear Cart"
        titleStyle={{ color: theme.colors.error }}
        leadingIcon={() => <Trash2 size={20} color={theme.colors.error} strokeWidth={2} />}
      />
    </Menu>
  );
}

const styles = StyleSheet.create({
  iconButton: { padding: spacing.xs, marginLeft: spacing.xs },
});
