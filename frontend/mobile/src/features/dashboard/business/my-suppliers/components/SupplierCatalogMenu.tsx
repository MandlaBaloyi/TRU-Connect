import React, { useState } from "react";
import { Pressable, StyleSheet } from "react-native";
import { Divider, Menu, useTheme } from "react-native-paper";
import { MessageCircle, MoreVertical, Store, TriangleAlert, UserX } from "lucide-react-native";

import { spacing } from "@/theme/spacing";

interface Props {
  onViewProfile: () => void;
  onContactSupplier: () => void;
  onReport: () => void;
  onDisconnect: () => void;
}

/** Mirrors supplier/products/components/ProductsOverflowMenu.tsx
 *  exactly -- same react-native-paper Menu, same icon-button anchor
 *  sizing/weight, own open/closed state internally so the screen only
 *  supplies what each action DOES.
 *
 * Order is deliberate, least-to-most consequential: profile info
 * first, then contact, then the two "something's wrong" actions --
 * Disconnect last and visually marked destructive (error-coloured
 * text, a Divider above it), same convention this app already uses
 * everywhere a destructive action sits in a menu.
 */
export function SupplierCatalogMenu({ onViewProfile, onContactSupplier, onReport, onDisconnect }: Props) {
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
        onPress={() => runAndClose(onViewProfile)}
        title="View Supplier Profile"
        leadingIcon={({ size, color }) => <Store size={size} color={color} strokeWidth={2} />}
      />
      <Menu.Item
        onPress={() => runAndClose(onContactSupplier)}
        title="Contact Supplier"
        leadingIcon={({ size, color }) => <MessageCircle size={size} color={color} strokeWidth={2} />}
      />
      <Menu.Item
        onPress={() => runAndClose(onReport)}
        title="Report"
        leadingIcon={({ size, color }) => <TriangleAlert size={size} color={color} strokeWidth={2} />}
      />
      <Divider />
      <Menu.Item
        onPress={() => runAndClose(onDisconnect)}
        title="Disconnect from this Supplier"
        titleStyle={{ color: theme.colors.error }}
        leadingIcon={() => <UserX size={20} color={theme.colors.error} strokeWidth={2} />}
      />
    </Menu>
  );
}

const styles = StyleSheet.create({
  iconButton: { padding: spacing.xs, marginLeft: spacing.xs },
});
